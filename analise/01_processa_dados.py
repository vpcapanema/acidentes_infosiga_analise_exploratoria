"""Processa CSVs do Infosiga e gera agregados em Parquet/JSON.

Saídas em analise/out/:
  - sinistros.parquet  (sinistros enriquecidos, todos os anos)
  - pessoas.parquet    (pessoas/vítimas)
  - agg_*.json         (agregações pré-computadas)
  - eventos_rodovias.parquet (eventos com coordenadas, para analise geográfica)
"""
from __future__ import annotations

import json
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"d:\acidentes_infosiga_analise_exploratoria")
DATA = ROOT / "dados" / "dados_infosiga"
OUT = ROOT / "analise" / "out"
OUT.mkdir(parents=True, exist_ok=True)


def strip_accents(s: str) -> str:
    if not isinstance(s, str):
        return s
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


# -------------------------- SINISTROS --------------------------

SIN_COLS = [
    "id_sinistro", "tipo_registro", "data_sinistro", "ano_sinistro", "mes_sinistro",
    "dia_sinistro", "hora_sinistro", "dia_da_semana", "turno", "logradouro",
    "tipo_via", "tipo_local", "latitude", "longitude", "cod_ibge", "municipio",
    "regiao_administrativa", "administracao", "conservacao", "circunscricao",
    "tp_sinistro_primario",
    "qtd_pedestre", "qtd_bicicleta", "qtd_motocicleta", "qtd_automovel",
    "qtd_onibus", "qtd_caminhao", "qtd_veic_outros", "qtd_veic_nao_disponivel",
    "qtd_gravidade_fatal", "qtd_gravidade_grave", "qtd_gravidade_leve",
    "qtd_gravidade_ileso", "qtd_gravidade_nao_disponivel",
    "tp_sinistro_atropelamento", "tp_sinistro_colisao_frontal",
    "tp_sinistro_colisao_traseira", "tp_sinistro_colisao_lateral",
    "tp_sinistro_colisao_transversal", "tp_sinistro_colisao_outros",
    "tp_sinistro_choque", "tp_sinistro_capotamento", "tp_sinistro_engavetamento",
    "tp_sinistro_tombamento", "tp_sinistro_outros", "tp_sinistro_nao_disponivel",
]

QTD_COLS = [c for c in SIN_COLS if c.startswith("qtd_")]
TP_COLS = [c for c in SIN_COLS if c.startswith("tp_sinistro_") and c != "tp_sinistro_primario"]


def read_sinistros() -> pd.DataFrame:
    dfs = []
    for fn in ["sinistros_2015-2021.csv", "sinistros_2022-2026.csv"]:
        print(f"[sinistros] lendo {fn}...")
        df = pd.read_csv(
            DATA / fn,
            sep=";",
            encoding="latin-1",
            usecols=SIN_COLS,
            dtype={"id_sinistro": "Int64", "cod_ibge": "Int64",
                   "ano_sinistro": "Int16", "mes_sinistro": "Int8",
                   "dia_sinistro": "Int8"},
            low_memory=False,
        )
        dfs.append(df)
    df = pd.concat(dfs, ignore_index=True)
    print(f"[sinistros] total bruto: {len(df):,}")

    # Normaliza texto
    for c in ["tipo_registro", "dia_da_semana", "turno", "tipo_via", "tipo_local",
              "municipio", "regiao_administrativa", "administracao", "conservacao",
              "circunscricao", "tp_sinistro_primario"]:
        df[c] = df[c].astype("string").str.strip().map(strip_accents).str.upper()

    # Datas
    df["data_sinistro"] = pd.to_datetime(df["data_sinistro"], format="%d/%m/%Y", errors="coerce")
    df["hora_num"] = pd.to_numeric(df["hora_sinistro"].str.slice(0, 2), errors="coerce")

    # Coordenadas (decimal com vírgula)
    for c in ["latitude", "longitude"]:
        df[c] = pd.to_numeric(df[c].astype("string").str.replace(",", ".", regex=False), errors="coerce")
    # Sanitiza lat/long dentro do BBOX de SP
    mask_sp = df["latitude"].between(-25.5, -19.5) & df["longitude"].between(-53.5, -44.0)
    df.loc[~mask_sp, ["latitude", "longitude"]] = np.nan

    # Numéricos
    for c in QTD_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype("Int32")
    for c in TP_COLS:
        df[c] = (df[c].astype("string").str.upper().str.strip() == "S").fillna(False).astype("int8")

    # Derivadas
    df["total_vitimas"] = (df["qtd_gravidade_fatal"] + df["qtd_gravidade_grave"] +
                           df["qtd_gravidade_leve"] + df["qtd_gravidade_ileso"])
    df["tem_vitima"] = (df["qtd_gravidade_fatal"] + df["qtd_gravidade_grave"] +
                        df["qtd_gravidade_leve"]) > 0
    df["tem_fatal"] = df["qtd_gravidade_fatal"] > 0
    df["total_veiculos"] = (df["qtd_automovel"] + df["qtd_motocicleta"] + df["qtd_bicicleta"] +
                            df["qtd_onibus"] + df["qtd_caminhao"] + df["qtd_veic_outros"])

    # Flag de rodovia (estadual / federal)
    df["em_rodovia"] = df["tipo_via"].fillna("").str.contains("ESTRADA|RODOVIA", regex=True)
    df["em_rodovia_estadual"] = (df["administracao"].fillna("").str.contains("DER|CONCESSIONARIA|ARTESP|ESTADO", regex=True)
                                  | df["conservacao"].fillna("").str.contains("DER|CONCESSIONARIA", regex=True))

    return df


# -------------------------- PESSOAS --------------------------

PES_COLS = [
    "id_sinistro", "cod_ibge", "municipio", "regiao_administrativa", "tipo_via",
    "tipo_veiculo_vitima", "sexo", "idade", "gravidade_lesao", "tipo_de_vitima",
    "faixa_etaria_demografica", "ano_sinistro", "mes_sinistro", "ano_obito",
    "local_obito", "local_via", "tempo_sinistro_obito",
]


def read_pessoas() -> pd.DataFrame:
    dfs = []
    for fn in ["pessoas_2015-2021.csv", "pessoas_2022-2026.csv"]:
        print(f"[pessoas] lendo {fn}...")
        df = pd.read_csv(
            DATA / fn,
            sep=";",
            encoding="latin-1",
            usecols=PES_COLS,
            dtype={"id_sinistro": "Int64", "cod_ibge": "Int64",
                   "ano_sinistro": "Int16", "idade": "Int16"},
            low_memory=False,
        )
        dfs.append(df)
    df = pd.concat(dfs, ignore_index=True)
    for c in ["tipo_via", "tipo_veiculo_vitima", "sexo", "gravidade_lesao",
              "tipo_de_vitima", "faixa_etaria_demografica", "local_obito",
              "local_via", "regiao_administrativa", "municipio"]:
        df[c] = df[c].astype("string").str.strip().map(strip_accents).str.upper()
    print(f"[pessoas] total: {len(df):,}")
    return df


# -------------------------- AGREGAÇÕES --------------------------

def agg_por_ano(sin: pd.DataFrame, pes: pd.DataFrame) -> dict:
    g = sin.groupby("ano_sinistro").agg(
        sinistros=("id_sinistro", "count"),
        com_vitima=("tem_vitima", "sum"),
        fatais=("tem_fatal", "sum"),
        vitimas_fatais=("qtd_gravidade_fatal", "sum"),
        vitimas_graves=("qtd_gravidade_grave", "sum"),
        vitimas_leves=("qtd_gravidade_leve", "sum"),
        ilesos=("qtd_gravidade_ileso", "sum"),
    ).reset_index()
    g["total_vitimas"] = g["vitimas_fatais"] + g["vitimas_graves"] + g["vitimas_leves"]

    # vítimas (registro de pessoas) por ano
    gv = pes.groupby("ano_sinistro").size().rename("pessoas_envolvidas").reset_index()
    g = g.merge(gv, on="ano_sinistro", how="left")
    return g.to_dict(orient="list")


def agg_mes(sin: pd.DataFrame) -> dict:
    g = sin.groupby(["ano_sinistro", "mes_sinistro"]).agg(
        sinistros=("id_sinistro", "count"),
        fatais=("qtd_gravidade_fatal", "sum"),
    ).reset_index()
    return g.to_dict(orient="list")


def agg_dia_semana(sin: pd.DataFrame) -> dict:
    ordem = ["SEGUNDA-FEIRA", "TERCA-FEIRA", "QUARTA-FEIRA", "QUINTA-FEIRA",
             "SEXTA-FEIRA", "SABADO", "DOMINGO"]
    g = sin.groupby("dia_da_semana").agg(
        sinistros=("id_sinistro", "count"),
        fatais=("qtd_gravidade_fatal", "sum"),
    ).reindex(ordem).reset_index()
    return g.to_dict(orient="list")


def agg_turno(sin: pd.DataFrame) -> dict:
    g = sin.groupby("turno").agg(
        sinistros=("id_sinistro", "count"),
        fatais=("qtd_gravidade_fatal", "sum"),
    ).reset_index()
    return g.to_dict(orient="list")


def agg_hora(sin: pd.DataFrame) -> dict:
    g = sin.groupby("hora_num").agg(
        sinistros=("id_sinistro", "count"),
        fatais=("qtd_gravidade_fatal", "sum"),
    ).reset_index()
    g = g.dropna()
    g["hora_num"] = g["hora_num"].astype(int)
    return g.to_dict(orient="list")


def agg_tipo_sinistro(sin: pd.DataFrame) -> dict:
    g = sin.groupby("tp_sinistro_primario").agg(
        sinistros=("id_sinistro", "count"),
        fatais=("qtd_gravidade_fatal", "sum"),
        graves=("qtd_gravidade_grave", "sum"),
    ).reset_index().sort_values("sinistros", ascending=False)
    return g.to_dict(orient="list")


def agg_tipo_via(sin: pd.DataFrame) -> dict:
    g = sin.groupby("tipo_via").agg(
        sinistros=("id_sinistro", "count"),
        fatais=("qtd_gravidade_fatal", "sum"),
    ).reset_index().sort_values("sinistros", ascending=False)
    return g.to_dict(orient="list")


def agg_administracao(sin: pd.DataFrame) -> dict:
    g = sin.groupby("administracao").agg(
        sinistros=("id_sinistro", "count"),
        fatais=("qtd_gravidade_fatal", "sum"),
    ).reset_index().sort_values("sinistros", ascending=False)
    return g.to_dict(orient="list")


def agg_regiao(sin: pd.DataFrame) -> dict:
    g = sin.groupby("regiao_administrativa").agg(
        sinistros=("id_sinistro", "count"),
        fatais=("qtd_gravidade_fatal", "sum"),
        graves=("qtd_gravidade_grave", "sum"),
    ).reset_index().sort_values("sinistros", ascending=False)
    return g.to_dict(orient="list")


def agg_municipios(sin: pd.DataFrame, top: int = 30) -> dict:
    g = sin.groupby(["municipio", "cod_ibge"]).agg(
        sinistros=("id_sinistro", "count"),
        fatais=("qtd_gravidade_fatal", "sum"),
    ).reset_index().sort_values("fatais", ascending=False).head(top)
    return g.to_dict(orient="list")


def agg_modo(sin: pd.DataFrame) -> dict:
    tot = {
        "Automóvel": int(sin["qtd_automovel"].sum()),
        "Motocicleta": int(sin["qtd_motocicleta"].sum()),
        "Bicicleta": int(sin["qtd_bicicleta"].sum()),
        "Ônibus": int(sin["qtd_onibus"].sum()),
        "Caminhão": int(sin["qtd_caminhao"].sum()),
        "Pedestre": int(sin["qtd_pedestre"].sum()),
        "Outros": int(sin["qtd_veic_outros"].sum()),
    }
    return tot


def agg_pessoas_demografia(pes: pd.DataFrame) -> dict:
    out = {}
    out["sexo"] = pes.groupby("sexo").size().rename("n").reset_index().to_dict(orient="list")
    out["gravidade"] = pes.groupby("gravidade_lesao").size().rename("n").reset_index().to_dict(orient="list")
    out["tipo_vitima"] = pes.groupby("tipo_de_vitima").size().rename("n").reset_index().to_dict(orient="list")
    out["tipo_veiculo_vitima"] = (pes.groupby("tipo_veiculo_vitima").size()
                                   .rename("n").reset_index()
                                   .sort_values("n", ascending=False).head(15).to_dict(orient="list"))
    out["faixa_etaria"] = pes.groupby("faixa_etaria_demografica").size().rename("n").reset_index().to_dict(orient="list")
    # Obitos por ano
    ob = pes[pes["gravidade_lesao"] == "FATAL"]
    out["obitos_por_ano"] = ob.groupby("ano_sinistro").size().rename("n").reset_index().to_dict(orient="list")
    out["obitos_sexo_faixa"] = (ob.groupby(["sexo", "faixa_etaria_demografica"]).size()
                                  .rename("n").reset_index().to_dict(orient="list"))
    out["obitos_tipo_vitima"] = (ob.groupby("tipo_de_vitima").size()
                                   .rename("n").reset_index()
                                   .sort_values("n", ascending=False).to_dict(orient="list"))
    # Tempo sinistro -> óbito
    tso = pd.to_numeric(pes["tempo_sinistro_obito"], errors="coerce")
    out["tempo_obito_hist"] = {
        "values": tso.dropna().clip(upper=180).round().astype(int).value_counts().sort_index().to_dict()
    }
    return out


# -------------------------- MAIN --------------------------

def main():
    sin = read_sinistros()
    pes = read_pessoas()

    print("[agg] ano..."); json.dump(agg_por_ano(sin, pes), open(OUT / "agg_ano.json", "w"), default=int)
    print("[agg] mes..."); json.dump(agg_mes(sin), open(OUT / "agg_mes.json", "w"), default=int)
    print("[agg] dia_semana..."); json.dump(agg_dia_semana(sin), open(OUT / "agg_dia_semana.json", "w"), default=int)
    print("[agg] turno..."); json.dump(agg_turno(sin), open(OUT / "agg_turno.json", "w"), default=int)
    print("[agg] hora..."); json.dump(agg_hora(sin), open(OUT / "agg_hora.json", "w"), default=int)
    print("[agg] tipo_sinistro..."); json.dump(agg_tipo_sinistro(sin), open(OUT / "agg_tipo_sinistro.json", "w"), default=int)
    print("[agg] tipo_via..."); json.dump(agg_tipo_via(sin), open(OUT / "agg_tipo_via.json", "w"), default=int)
    print("[agg] administracao..."); json.dump(agg_administracao(sin), open(OUT / "agg_administracao.json", "w"), default=int)
    print("[agg] regiao..."); json.dump(agg_regiao(sin), open(OUT / "agg_regiao.json", "w"), default=int)
    print("[agg] municipios..."); json.dump(agg_municipios(sin), open(OUT / "agg_municipios.json", "w"), default=int)
    print("[agg] modo..."); json.dump(agg_modo(sin), open(OUT / "agg_modo.json", "w"), default=int)
    print("[agg] pessoas..."); json.dump(agg_pessoas_demografia(pes), open(OUT / "agg_pessoas.json", "w"), default=int)

    # KPIs globais
    kpi = {
        "total_sinistros": int(len(sin)),
        "total_sinistros_com_vitima": int(sin["tem_vitima"].sum()),
        "total_sinistros_fatais": int(sin["tem_fatal"].sum()),
        "total_obitos": int(sin["qtd_gravidade_fatal"].sum()),
        "total_graves": int(sin["qtd_gravidade_grave"].sum()),
        "total_leves": int(sin["qtd_gravidade_leve"].sum()),
        "total_ilesos": int(sin["qtd_gravidade_ileso"].sum()),
        "total_pessoas": int(len(pes)),
        "ano_min": int(sin["ano_sinistro"].min()),
        "ano_max": int(sin["ano_sinistro"].max()),
        "perc_com_coord": float((sin["latitude"].notna()).mean() * 100),
        "perc_em_rodovia": float(sin["em_rodovia"].mean() * 100),
    }
    json.dump(kpi, open(OUT / "kpi.json", "w"), default=int)
    print("[kpi]", kpi)

    # Eventos georreferenciados — salvar apenas o necessário p/ análise geográfica
    print("[geo] salvando eventos_rodovias.parquet...")
    cols_geo = ["id_sinistro", "ano_sinistro", "mes_sinistro", "data_sinistro",
                "latitude", "longitude", "logradouro", "municipio",
                "regiao_administrativa", "administracao", "conservacao",
                "tp_sinistro_primario", "tem_vitima", "tem_fatal",
                "qtd_gravidade_fatal", "qtd_gravidade_grave", "qtd_gravidade_leve",
                "em_rodovia", "em_rodovia_estadual"]
    geo = sin.loc[sin["latitude"].notna() & sin["em_rodovia"], cols_geo].copy()
    geo.to_parquet(OUT / "eventos_rodovias.parquet", index=False)
    print(f"[geo] {len(geo):,} eventos em rodovias com coordenadas")

    # salvar sinistros enxuto para outros usos
    sin[["id_sinistro", "ano_sinistro", "mes_sinistro", "data_sinistro",
         "dia_da_semana", "turno", "hora_num", "tipo_via", "tipo_local",
         "regiao_administrativa", "municipio", "administracao",
         "tp_sinistro_primario", "qtd_gravidade_fatal", "qtd_gravidade_grave",
         "qtd_gravidade_leve", "qtd_gravidade_ileso", "tem_vitima", "tem_fatal",
         "em_rodovia", "latitude", "longitude"]].to_parquet(OUT / "sinistros.parquet", index=False)
    pes.to_parquet(OUT / "pessoas.parquet", index=False)
    print("OK")


if __name__ == "__main__":
    main()
