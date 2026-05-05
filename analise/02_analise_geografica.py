"""Análise geográfica: cruza eventos em rodovias com a malha DER.

Saídas em analise/out/:
  - rodovias_rank.json      (top rodovias por sinistros, óbitos, risco)
  - trechos_rank.json       (top trechos/subtrechos)
  - malha_topN.geojson      (linhas das top/bottom rodovias)
  - eventos_amostra.geojson (amostra de pontos p/ mapa)
  - heat_points.json        (pontos para heatmap)
"""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

ROOT = Path(r"d:\acidentes_infosiga_analise_exploratoria")
OUT = ROOT / "analise" / "out"
MALHA = ROOT / "dados" / "Sistema Rodoviário Estadual" / "MALHA_RODOVIARIA.shp"

print("Carregando malha DER...")
malha = gpd.read_file(MALHA)
malha = malha[malha.geometry.notna() & ~malha.geometry.is_empty].copy()
malha["Rodovia"] = malha["Rodovia"].astype(str).str.strip().str.upper()

def categoria_der(v):
    s = str(v or "").strip().upper()
    if s.startswith("SPA"):
        return "SPA"
    if s.startswith("SPI"):
        return "SPI"
    if s.startswith("SPM"):
        return "SPM"
    if s.startswith("SP"):
        return "SP"
    return "OUTRAS"

malha["categoria_der"] = malha["Rodovia"].apply(categoria_der)
# Nome único de trecho
malha["trecho_id"] = malha["Subtrecho"].fillna("").astype(str) + " | " + malha["Rodovia"].astype(str) + " km " + malha["KmInicial"].round(2).astype(str) + "-" + malha["KmFinal"].round(2).astype(str)
malha["Extensao"] = pd.to_numeric(malha["Extensao"], errors="coerce")
print(f"  {len(malha):,} trechos, CRS={malha.crs}")

print("Carregando eventos em rodovias...")
df = pd.read_parquet(OUT / "eventos_rodovias.parquet")
print(f"  {len(df):,} eventos")

# GeoDataFrame de eventos em WGS84 -> reprojeta p/ CRS da malha (5880)
pts = gpd.GeoDataFrame(
    df,
    geometry=[Point(xy) for xy in zip(df.longitude, df.latitude)],
    crs="EPSG:4326",
).to_crs(malha.crs)

# Spatial join — ponto mais próximo até 300m
print("Join espacial (nearest, tol=300m)...")
joined = gpd.sjoin_nearest(
    pts,
    malha[["Rodovia", "trecho_id", "KmInicial", "KmFinal", "Extensao",
           "SedeRegion", "Jurisdicao", "Administra", "geometry"]],
    how="left",
    max_distance=300,
    distance_col="dist_m",
)
joined = joined[joined["Rodovia"].notna()].copy()
joined["administracao"] = joined["Administra"].astype(str).str.strip().str.upper().replace("NAN", "NÃO INFORMADO")
print(f"  {len(joined):,} eventos associados a algum trecho (<=300m)")


def normaliza_tipo_evento(v):
    s = str(v or "").strip().upper()
    if "ATROPEL" in s:
        return "ATROPELAMENTO"
    if "CHOQUE" in s:
        return "CHOQUE"
    if "COLISAO" in s:
        return "COLISAO"
    return "OUTROS"


joined["evento_tipo"] = joined["tp_sinistro_primario"].apply(normaliza_tipo_evento)

# --------- RANKING POR RODOVIA ---------
ext_rodovia = malha.groupby("Rodovia", as_index=False)["Extensao"].sum().rename(columns={"Extensao": "km_total"})
adm_rodovia = joined.groupby("Rodovia")["administracao"].agg(lambda x: x.mode()[0] if len(x) else "NÃO INFORMADO").reset_index()
r = joined.groupby("Rodovia").agg(
    sinistros=("id_sinistro", "count"),
    obitos=("qtd_gravidade_fatal", "sum"),
    graves=("qtd_gravidade_grave", "sum"),
    com_vitima=("tem_vitima", "sum"),
    fatais=("tem_fatal", "sum"),
).reset_index().merge(ext_rodovia, on="Rodovia", how="left").merge(adm_rodovia, on="Rodovia", how="left")
r["sinistros_por_km"] = r["sinistros"] / r["km_total"].replace(0, pd.NA)
r["obitos_por_km"] = r["obitos"] / r["km_total"].replace(0, pd.NA)
r["indice_letalidade"] = (r["obitos"] / r["sinistros"].replace(0, pd.NA) * 100)

r = r.sort_values("sinistros", ascending=False)

r_ano = joined.groupby(["ano_sinistro", "Rodovia"]).agg(
    sinistros=("id_sinistro", "count"),
    obitos=("qtd_gravidade_fatal", "sum"),
    graves=("qtd_gravidade_grave", "sum"),
    com_vitima=("tem_vitima", "sum"),
    fatais=("tem_fatal", "sum"),
).reset_index().merge(ext_rodovia, on="Rodovia", how="left")
r_ano["sinistros_por_km"] = r_ano["sinistros"] / r_ano["km_total"].replace(0, pd.NA)
r_ano["obitos_por_km"] = r_ano["obitos"] / r_ano["km_total"].replace(0, pd.NA)
r_ano["indice_letalidade"] = r_ano["obitos"] / r_ano["sinistros"].replace(0, pd.NA) * 100

r_tipo = joined.groupby(["evento_tipo", "Rodovia"]).agg(
    sinistros=("id_sinistro", "count"),
    obitos=("qtd_gravidade_fatal", "sum"),
    graves=("qtd_gravidade_grave", "sum"),
).reset_index().merge(ext_rodovia, on="Rodovia", how="left")
r_tipo["sinistros_por_km"] = r_tipo["sinistros"] / r_tipo["km_total"].replace(0, pd.NA)
r_tipo["obitos_por_km"] = r_tipo["obitos"] / r_tipo["km_total"].replace(0, pd.NA)
r_tipo["indice_letalidade"] = r_tipo["obitos"] / r_tipo["sinistros"].replace(0, pd.NA) * 100

r_ano_tipo = joined.groupby(["ano_sinistro", "Rodovia", "evento_tipo"]).agg(
    sinistros=("id_sinistro", "count"),
    obitos=("qtd_gravidade_fatal", "sum"),
    graves=("qtd_gravidade_grave", "sum"),
).reset_index().merge(ext_rodovia, on="Rodovia", how="left")
r_ano_tipo["sinistros_por_km"] = r_ano_tipo["sinistros"] / r_ano_tipo["km_total"].replace(0, pd.NA)
r_ano_tipo["obitos_por_km"] = r_ano_tipo["obitos"] / r_ano_tipo["km_total"].replace(0, pd.NA)
r_ano_tipo["indice_letalidade"] = r_ano_tipo["obitos"] / r_ano_tipo["sinistros"].replace(0, pd.NA) * 100


def df_to_records(df):
    return json.loads(df.to_json(orient="records", force_ascii=False))

top10_by_type = {}
focus_roads = set()
for evento_tipo, g in r_tipo.groupby("evento_tipo"):
    top_rows = g.sort_values(["sinistros", "obitos"], ascending=False).head(10)
    top10_by_type[evento_tipo] = df_to_records(top_rows)
    focus_roads.update(top_rows["Rodovia"].tolist())

rod_json = {
    "top10_sinistros": df_to_records(r.head(10)),
    "bottom10_sinistros": df_to_records(r[r["sinistros"] >= 5].tail(10).sort_values("sinistros")),
    "top10_obitos": df_to_records(r.sort_values("obitos", ascending=False).head(10)),
    "top10_densidade": df_to_records(r[r["km_total"] >= 20].sort_values("sinistros_por_km", ascending=False).head(10)),
    "top10_letalidade": df_to_records(r[r["sinistros"] >= 100].sort_values("indice_letalidade", ascending=False).head(10)),
    "top10_by_type": top10_by_type,
    "all": df_to_records(r),
    "all_by_year": df_to_records(r_ano),
    "all_by_year_type": df_to_records(r_ano_tipo),
}
json.dump(rod_json, open(OUT / "rodovias_rank.json", "w", encoding="utf-8"), ensure_ascii=False)
print(f"  {len(r)} rodovias rankeadas")

# --------- RANKING POR TRECHO ---------
adm_trecho = joined.groupby("trecho_id")["administracao"].agg(lambda x: x.mode()[0] if len(x) else "NÃO INFORMADO").reset_index()

t = joined.groupby(["Rodovia", "trecho_id", "KmInicial", "KmFinal", "Extensao"]).agg(
    sinistros=("id_sinistro", "count"),
    obitos=("qtd_gravidade_fatal", "sum"),
    graves=("qtd_gravidade_grave", "sum"),
).reset_index().merge(adm_trecho, on="trecho_id", how="left")
t["sinistros_por_km"] = t["sinistros"] / t["Extensao"].replace(0, pd.NA)
t["obitos_por_km"] = t["obitos"] / t["Extensao"].replace(0, pd.NA)
t["indice_letalidade"] = t["obitos"] / t["sinistros"].replace(0, pd.NA) * 100
t = t.sort_values("sinistros", ascending=False)

t_ano = joined.groupby(["ano_sinistro", "Rodovia", "trecho_id", "KmInicial", "KmFinal", "Extensao"]).agg(
    sinistros=("id_sinistro", "count"),
    obitos=("qtd_gravidade_fatal", "sum"),
    graves=("qtd_gravidade_grave", "sum"),
).reset_index().merge(adm_trecho, on="trecho_id", how="left")
t_ano["sinistros_por_km"] = t_ano["sinistros"] / t_ano["Extensao"].replace(0, pd.NA)
t_ano["obitos_por_km"] = t_ano["obitos"] / t_ano["Extensao"].replace(0, pd.NA)
t_ano["indice_letalidade"] = t_ano["obitos"] / t_ano["sinistros"].replace(0, pd.NA) * 100

t_tipo = joined.groupby(["Rodovia", "trecho_id", "KmInicial", "KmFinal", "Extensao", "evento_tipo"]).agg(
    sinistros=("id_sinistro", "count"),
    obitos=("qtd_gravidade_fatal", "sum"),
    graves=("qtd_gravidade_grave", "sum"),
).reset_index().merge(adm_trecho, on="trecho_id", how="left")
t_tipo["sinistros_por_km"] = t_tipo["sinistros"] / t_tipo["Extensao"].replace(0, pd.NA)
t_tipo["obitos_por_km"] = t_tipo["obitos"] / t_tipo["Extensao"].replace(0, pd.NA)
t_tipo["indice_letalidade"] = t_tipo["obitos"] / t_tipo["sinistros"].replace(0, pd.NA) * 100

t_ano_tipo = joined.groupby(["ano_sinistro", "Rodovia", "trecho_id", "KmInicial", "KmFinal", "Extensao", "evento_tipo"]).agg(
    sinistros=("id_sinistro", "count"),
    obitos=("qtd_gravidade_fatal", "sum"),
    graves=("qtd_gravidade_grave", "sum"),
).reset_index().merge(adm_trecho, on="trecho_id", how="left")
t_ano_tipo["sinistros_por_km"] = t_ano_tipo["sinistros"] / t_ano_tipo["Extensao"].replace(0, pd.NA)
t_ano_tipo["obitos_por_km"] = t_ano_tipo["obitos"] / t_ano_tipo["Extensao"].replace(0, pd.NA)
t_ano_tipo["indice_letalidade"] = t_ano_tipo["obitos"] / t_ano_tipo["sinistros"].replace(0, pd.NA) * 100

trecho_json = {
    "top10_sinistros": df_to_records(t.head(10)),
    "top10_obitos": df_to_records(t.sort_values("obitos", ascending=False).head(10)),
    "top10_densidade": df_to_records(t[t["Extensao"] >= 1].sort_values("sinistros_por_km", ascending=False).head(10)),
    "top10_obitos_km": df_to_records(t[t["Extensao"] >= 1].sort_values("obitos_por_km", ascending=False).head(10)),
    "all": df_to_records(t),
    "all_by_year": df_to_records(t_ano),
    "all_by_type": df_to_records(t_tipo),
    "all_by_year_type": df_to_records(t_ano_tipo),
}
# trechos das top-rodovias — top 10 trechos dentro da rodovia campeã
top_rod = r.iloc[0]["Rodovia"]
trecho_json[f"top10_trechos_rodovia_campea"] = {
    "rodovia": top_rod,
    "trechos": df_to_records(t[t["Rodovia"] == top_rod].head(10)),
}
json.dump(trecho_json, open(OUT / "trechos_rank.json", "w", encoding="utf-8"), ensure_ascii=False)

# --------- COMPARATIVO POR ADMINISTRAÇÃO ---------
# Agrega por administracao × evento_tipo × ano para alimentar o painel comparativo
comp_adm_tipo = joined.groupby(["administracao", "evento_tipo"]).agg(
    sinistros=("id_sinistro", "count"),
    obitos=("qtd_gravidade_fatal", "sum"),
    graves=("qtd_gravidade_grave", "sum"),
    km_total=("Extensao", "sum"),
).reset_index()
comp_adm_tipo["sinistros_por_km"] = comp_adm_tipo["sinistros"] / comp_adm_tipo["km_total"].replace(0, pd.NA)
comp_adm_tipo["obitos_por_km"] = comp_adm_tipo["obitos"] / comp_adm_tipo["km_total"].replace(0, pd.NA)
comp_adm_tipo["indice_letalidade"] = comp_adm_tipo["obitos"] / comp_adm_tipo["sinistros"].replace(0, pd.NA) * 100

comp_adm_ano = joined.groupby(["administracao", "ano_sinistro"]).agg(
    sinistros=("id_sinistro", "count"),
    obitos=("qtd_gravidade_fatal", "sum"),
    graves=("qtd_gravidade_grave", "sum"),
    km_total=("Extensao", "sum"),
).reset_index()
comp_adm_ano["sinistros_por_km"] = comp_adm_ano["sinistros"] / comp_adm_ano["km_total"].replace(0, pd.NA)
comp_adm_ano["obitos_por_km"] = comp_adm_ano["obitos"] / comp_adm_ano["km_total"].replace(0, pd.NA)
comp_adm_ano["indice_letalidade"] = comp_adm_ano["obitos"] / comp_adm_ano["sinistros"].replace(0, pd.NA) * 100

comp_adm_ano_tipo = joined.groupby(["administracao", "ano_sinistro", "evento_tipo"]).agg(
    sinistros=("id_sinistro", "count"),
    obitos=("qtd_gravidade_fatal", "sum"),
    graves=("qtd_gravidade_grave", "sum"),
    km_total=("Extensao", "sum"),
).reset_index()
comp_adm_ano_tipo["sinistros_por_km"] = comp_adm_ano_tipo["sinistros"] / comp_adm_ano_tipo["km_total"].replace(0, pd.NA)
comp_adm_ano_tipo["obitos_por_km"] = comp_adm_ano_tipo["obitos"] / comp_adm_ano_tipo["km_total"].replace(0, pd.NA)
comp_adm_ano_tipo["indice_letalidade"] = comp_adm_ano_tipo["obitos"] / comp_adm_ano_tipo["sinistros"].replace(0, pd.NA) * 100

comp_adm_trecho = t[["administracao", "Rodovia", "trecho_id", "KmInicial", "KmFinal", "Extensao",
                      "sinistros", "obitos", "graves", "sinistros_por_km", "obitos_por_km", "indice_letalidade"]].copy()

comp_json = {
    "byTipo": df_to_records(comp_adm_tipo),
    "byAno": df_to_records(comp_adm_ano),
    "byAnoTipo": df_to_records(comp_adm_ano_tipo),
    "trechos": df_to_records(comp_adm_trecho),
}
json.dump(comp_json, open(OUT / "comp_adm.json", "w", encoding="utf-8"), ensure_ascii=False)
print(f"  comp_adm.json: {len(comp_adm_tipo)} combinações adm×tipo")

subtrecho_store = {
    "unidade_espacial_minima": "subtrecho",
    "top10_rodovias_por_tipo": top10_by_type,
    "rodovias_foco": sorted(focus_roads),
    "subtrechos_all": df_to_records(t),
    "subtrechos_all_by_year": df_to_records(t_ano),
    "subtrechos_all_by_type": df_to_records(t_tipo),
    "subtrechos_all_by_year_type": df_to_records(t_ano_tipo),
    "subtrechos_foco": df_to_records(t[t["Rodovia"].isin(focus_roads)]),
    "subtrechos_foco_by_type": df_to_records(t_tipo[t_tipo["Rodovia"].isin(focus_roads)]),
    "subtrechos_foco_by_year_type": df_to_records(t_ano_tipo[t_ano_tipo["Rodovia"].isin(focus_roads)]),
}
json.dump(subtrecho_store, open(OUT / "subtrechos_analise.json", "w", encoding="utf-8"), ensure_ascii=False)

# --------- GEOJSON PARA MAPAS ---------
print("Gerando GeoJSONs...")
# Malha completa do DER em WGS84, preservando todos os trechos da base
malha_top = malha.copy()
malha_top["geometry"] = malha_top.geometry.simplify(30, preserve_topology=True)
malha_top_wgs = malha_top.to_crs(4326)
# Agrega por trecho DER para preservar a variabilidade espacial dentro da rodovia
stats_map = t[["trecho_id", "sinistros", "obitos", "graves", "sinistros_por_km", "obitos_por_km", "indice_letalidade"]]
malha_top_wgs = malha_top_wgs.merge(stats_map, on="trecho_id", how="left")
for c in ["sinistros", "obitos", "graves", "sinistros_por_km", "obitos_por_km", "indice_letalidade"]:
    malha_top_wgs[c] = malha_top_wgs[c].fillna(0)
cols = ["Rodovia", "categoria_der", "Municipio", "Administra", "Subtrecho", "trecho_id", "KmInicial", "KmFinal", "Extensao",
        "sinistros", "obitos", "graves", "sinistros_por_km", "obitos_por_km", "indice_letalidade", "geometry"]
malha_top_wgs[cols].to_file(OUT / "malha_topN.geojson", driver="GeoJSON")

# Pontos e heatmaps para camadas do Leaflet
pts_fatais = joined[joined["tem_fatal"]].copy()
print(f"  fatais: {len(pts_fatais)}")
pts_sinistros = joined.sample(n=min(12000, len(joined)), random_state=42).copy()
pts_com_vit = joined[joined["tem_vitima"] & ~joined["tem_fatal"]].sample(
    n=min(5000, int((joined["tem_vitima"] & ~joined["tem_fatal"]).sum())), random_state=42)

def pts_to_geojson(dfp, path):
    gdf = gpd.GeoDataFrame(
        dfp[["id_sinistro", "ano_sinistro", "municipio", "Rodovia", "evento_tipo", "tp_sinistro_primario",
             "qtd_gravidade_fatal", "qtd_gravidade_grave", "qtd_gravidade_leve"]],
        geometry=dfp.to_crs(4326).geometry,
        crs=4326,
    )
    gdf.to_file(path, driver="GeoJSON")

pts_to_geojson(pts_fatais, OUT / "pontos_fatais.geojson")
pts_to_geojson(pts_fatais, OUT / "pontos_obitos.geojson")
pts_to_geojson(pts_com_vit, OUT / "pontos_vitimas_amostra.geojson")
pts_to_geojson(pts_sinistros, OUT / "pontos_sinistros_amostra.geojson")

# Heat points separados por óbitos e sinistros
heat_sin = joined[["latitude", "longitude", "ano_sinistro"]].copy()
if len(heat_sin) > 40000:
    heat_sin = heat_sin.sample(40000, random_state=42)
json.dump({"points": heat_sin.round(5).values.tolist()}, open(OUT / "heat_points_sinistros.json", "w"))

heat_ob = joined[joined["tem_fatal"]][["latitude", "longitude", "qtd_gravidade_fatal", "ano_sinistro"]].copy()
if len(heat_ob) > 25000:
    heat_ob = heat_ob.sample(25000, random_state=42)
json.dump({"points": heat_ob.round(5).values.tolist()}, open(OUT / "heat_points_obitos.json", "w"))

# Compatibilidade com a saída antiga
json.dump({"points": heat_sin.round(5).values.tolist()}, open(OUT / "heat_points.json", "w"))

print("OK")
