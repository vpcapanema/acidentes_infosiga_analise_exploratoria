"""Gera a malha municipal usada pela escala espacial do dashboard.

A malha oficial 2025 do IBGE e baixada quando ainda nao existe em ``dados/``.
Cada trecho rodoviario recebe ``CD_MUN`` e ``NM_MUN`` por spatial join com os
poligonos municipais. Quando uma linha toca mais de um municipio, prevalece o
municipio que contem a maior extensao da linha, evitando duplicar os eventos do
trecho. O ativo final preserva os 645 poligonos oficiais (com geometria
simplificada para uso na web) e um mapa compacto ``trecho_id -> municipio``.
"""
from __future__ import annotations

import gzip
import json
import urllib.request
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
ROADS_PATH = ROOT / "dados" / "Sistema Rodoviário Estadual" / "MALHA_RODOVIARIA.shp"
IBGE_DIR = ROOT / "dados" / "ibge_municipios_2025"
IBGE_PATH = IBGE_DIR / "SP_Municipios_2025.shp"
IBGE_ZIP = IBGE_DIR / "SP_Municipios_2025.zip"
OUTPUT_PATH = ROOT / "docs" / "assets" / "geo" / "municipios_dashboard.json"
SOURCE_URL = (
    "https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/"
    "malhas_municipais/municipio_2025/UFs/SP/SP_Municipios_2025.zip"
)


def ensure_ibge_source() -> None:
    if IBGE_PATH.exists():
        return
    IBGE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Baixando malha municipal oficial: {SOURCE_URL}")
    urllib.request.urlretrieve(SOURCE_URL, IBGE_ZIP)
    with zipfile.ZipFile(IBGE_ZIP) as archive:
        archive.extractall(IBGE_DIR)
    if not IBGE_PATH.exists():
        raise FileNotFoundError(f"Shapefile municipal nao encontrado em {IBGE_PATH}")


def build_trecho_id(roads: gpd.GeoDataFrame) -> pd.Series:
    rodovia = roads["Rodovia"].astype(str).str.strip().str.upper()
    return (
        roads["Subtrecho"].fillna("").astype(str)
        + " | "
        + rodovia
        + " km "
        + pd.to_numeric(roads["KmInicial"], errors="coerce").round(2).astype(str)
        + "-"
        + pd.to_numeric(roads["KmFinal"], errors="coerce").round(2).astype(str)
    )


def main() -> None:
    ensure_ibge_source()

    roads = gpd.read_file(ROADS_PATH)
    roads = roads[roads.geometry.notna() & ~roads.geometry.is_empty].copy()
    roads["trecho_id"] = build_trecho_id(roads)
    if roads["trecho_id"].duplicated().any():
        duplicates = int(roads["trecho_id"].duplicated(keep=False).sum())
        raise ValueError(f"A malha possui {duplicates} trecho_id duplicados")

    municipalities = gpd.read_file(IBGE_PATH)[
        ["CD_MUN", "NM_MUN", "AREA_KM2", "geometry"]
    ].copy()
    municipalities = municipalities[
        municipalities.geometry.notna() & ~municipalities.geometry.is_empty
    ].copy()
    municipalities["CD_MUN"] = municipalities["CD_MUN"].astype(str)
    if len(municipalities) != 645 or municipalities["CD_MUN"].nunique() != 645:
        raise ValueError(
            "A malha oficial de Sao Paulo deve conter 645 municipios unicos; "
            f"foram encontrados {len(municipalities)} registros"
        )

    municipalities_roads_crs = municipalities.to_crs(roads.crs)
    roads_for_join = roads[["trecho_id", "geometry"]].copy()
    roads_for_join["road_index"] = range(len(roads_for_join))
    joined = gpd.sjoin(
        roads_for_join,
        municipalities_roads_crs[["CD_MUN", "NM_MUN", "geometry"]],
        how="left",
        predicate="intersects",
    )
    joined["overlap_m"] = [
        roads_for_join.iloc[int(road_index)].geometry.intersection(
            municipalities_roads_crs.loc[int(municipality_index)].geometry
        ).length
        if pd.notna(municipality_index)
        else 0.0
        for road_index, municipality_index in zip(
            joined["road_index"], joined["index_right"]
        )
    ]
    joined = (
        joined.sort_values(["road_index", "overlap_m"], ascending=[True, False])
        .drop_duplicates("road_index")
        .sort_values("road_index")
    )
    missing = joined["CD_MUN"].isna()
    if missing.any():
        raise ValueError(
            f"O spatial join deixou {int(missing.sum())} trechos sem municipio"
        )

    trecho_municipio = {
        trecho_id: [str(row.CD_MUN), str(row.NM_MUN)]
        for trecho_id, row in joined.set_index("trecho_id").iterrows()
    }

    # Simplificacao em CRS metrico para reduzir o ativo sem deformar divisas.
    web_municipalities = municipalities.to_crs(5880)
    web_municipalities.geometry = web_municipalities.geometry.simplify(
        75, preserve_topology=True
    )
    web_municipalities = web_municipalities.to_crs(4326)
    features = json.loads(web_municipalities.to_json(drop_id=True))["features"]

    payload = {
        "source": "IBGE - Malha Municipal Digital 2025",
        "sourceUrl": SOURCE_URL,
        "referenceYear": 2025,
        "municipios": {"type": "FeatureCollection", "features": features},
        "trechoMunicipio": trecho_municipio,
    }
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode(
        "utf-8"
    )
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_bytes(raw)
    OUTPUT_PATH.with_suffix(OUTPUT_PATH.suffix + ".gz").write_bytes(
        gzip.compress(raw, compresslevel=6)
    )

    print(f"Municipios: {len(features)}")
    print(f"Trechos associados: {len(trecho_municipio)}")
    print(f"Ativo: {OUTPUT_PATH} ({len(raw):,} bytes)")


if __name__ == "__main__":
    main()
