"""Gera as páginas HTML do dashboard Infosiga SP.

Páginas:
  docs/index.html                 (portal)
  docs/dashboard_principal.html   (29+ gráficos em 6 categorias)
  docs/RELATORIO_EXECUTIVO.html   (relatório analítico)
  docs/analise_geografica.html    (dashboard 1 — rodovias)
  docs/analise_subtrechos.html    (dashboard 2 — subtrechos)
  docs/GUIA_ACESSO.html           (navegação)
"""
# pylint: disable=too-many-lines
from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

ROOT = Path(r"d:\acidentes_infosiga_analise_exploratoria")
OUT = ROOT / "analise" / "out"
DOCS = ROOT / "docs"
ASSETS = DOCS / "assets"
DOCS.mkdir(exist_ok=True)
ASSETS.mkdir(exist_ok=True)


def write_json_asset(name, data):
    path = ASSETS / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    return f"assets/{name}"

# ================= CARREGA DADOS =================
def j(name):
    return json.load(open(OUT / name, encoding="utf-8"))

kpi = j("kpi.json")
ag_ano = pd.DataFrame(j("agg_ano.json"))
ag_mes = pd.DataFrame(j("agg_mes.json"))
ag_dia = pd.DataFrame(j("agg_dia_semana.json"))
ag_turno = pd.DataFrame(j("agg_turno.json"))
ag_hora = pd.DataFrame(j("agg_hora.json"))
ag_tp = pd.DataFrame(j("agg_tipo_sinistro.json"))
ag_via = pd.DataFrame(j("agg_tipo_via.json"))
ag_adm = pd.DataFrame(j("agg_administracao.json"))
ag_reg = pd.DataFrame(j("agg_regiao.json"))
ag_mun = pd.DataFrame(j("agg_municipios.json"))
ag_modo = j("agg_modo.json")
ag_pes = j("agg_pessoas.json")
rod = j("rodovias_rank.json")
trc = j("trechos_rank.json")
subtr = j("subtrechos_analise.json")

def br(n):
    """Formata número inteiro no padrão brasileiro (1.234.567)."""
    return f"{int(n):,}".replace(",", ".")


def pct(n, casas=1):
    """Formata percentual decimal no padrão brasileiro."""
    return f"{float(n):.{casas}f}".replace(".", ",")


# ================= PLOTLY THEME =================
pio.templates.default = "plotly_white"
COLORS = {
    "primary": "#0e4d92",       # azul SP
    "accent": "#d52b1e",        # vermelho SP
    "warn": "#f7b500",
    "ok": "#2e8b57",
    "muted": "#6b7280",
    "seq": ["#0e4d92", "#d52b1e", "#f7b500", "#2e8b57", "#7c3aed", "#0ea5e9", "#ea580c", "#065f46"],
}

PT_LABEL_MAP = {
    "NAO DISPONIVEL": "NÃO DISPONÍVEL",
    "COLISAO": "COLISÃO",
    "TERCA-FEIRA": "TERÇA-FEIRA",
    "SABADO": "SÁBADO",
    "MANHA": "MANHÃ",
    "ONIBUS": "ÔNIBUS",
    "CAMINHAO": "CAMINHÃO",
    "AUTOMOVEL": "AUTOMÓVEL",
    "CONCESSIONARIA": "CONCESSIONÁRIA",
    "RIBEIRAO PRETO": "RIBEIRÃO PRETO",
    "SAO JOSE DO RIO PRETO": "SÃO JOSÉ DO RIO PRETO",
    "SAO JOSE DOS CAMPOS": "SÃO JOSÉ DOS CAMPOS",
    "SAO PAULO": "SÃO PAULO",
    "SAO VICENTE": "SÃO VICENTE",
    "SAO BERNARDO DO CAMPO": "SÃO BERNARDO DO CAMPO",
    "SANTO ANDRE": "SANTO ANDRÉ",
    "JUNDIAI": "JUNDIAÍ",
    "TAUBATE": "TAUBATÉ",
    "ARACATUBA": "ARAÇATUBA",
    "MARILIA": "MARÍLIA",
    "INDICE LETALIDADE": "Índice de letalidade",
    "OBITOS POR KM": "Óbitos por km",
    "SINISTROS POR KM": "Sinistros por km",
}


def pt_label(value):
    if not isinstance(value, str):
        return value
    text = " ".join(value.replace("_", " ").split())
    if not text:
        return text
    mapped = PT_LABEL_MAP.get(text.upper())
    if mapped:
        return mapped
    for old, new in [
        ("NAO", "NÃO"),
        ("SAO", "SÃO"),
        ("JOSE", "JOSÉ"),
        ("JOAO", "JOÃO"),
        ("RIBEIRAO", "RIBEIRÃO"),
        ("CONCESSIONARIA", "CONCESSIONÁRIA"),
        ("AUTOMOVEL", "AUTOMÓVEL"),
        ("ONIBUS", "ÔNIBUS"),
        ("CAMINHAO", "CAMINHÃO"),
        ("COLISAO", "COLISÃO"),
        ("SABADO", "SÁBADO"),
        ("TERCA-FEIRA", "TERÇA-FEIRA"),
        ("MANHA", "MANHÃ"),
        ("ARACATUBA", "ARAÇATUBA"),
        ("MARILIA", "MARÍLIA"),
        ("JUNDIAI", "JUNDIAÍ"),
        ("TAUBATE", "TAUBATÉ"),
        ("SANTO ANDRE", "SANTO ANDRÉ"),
    ]:
        text = text.replace(old, new).replace(old.title(), new.title())
    return text


def wrap_title(text, width=34):
    if not isinstance(text, str):
        return text
    clean = " ".join(text.replace("<br>", " ").split())
    if len(clean) <= width:
        return clean
    return "<br>".join(textwrap.wrap(clean, width=width, break_long_words=False, break_on_hyphens=False))


def _normalize_seq(values):
    if values is None:
        return values
    try:
        seq = list(values)
    except TypeError:
        return values
    if not any(isinstance(v, str) for v in seq):
        return values
    return [pt_label(v) if isinstance(v, str) else v for v in seq]


def apply_pt_formatting(fig):
    title_text = getattr(getattr(fig.layout, "title", None), "text", None)
    if title_text:
        fig.update_layout(title=dict(text=f"<b>{wrap_title(pt_label(title_text))}</b>", x=0.5, xanchor="center"))
    if getattr(fig.layout.xaxis.title, "text", None):
        fig.update_xaxes(title_text=pt_label(fig.layout.xaxis.title.text))
    if getattr(fig.layout.yaxis.title, "text", None):
        fig.update_yaxes(title_text=pt_label(fig.layout.yaxis.title.text))
    for tr in fig.data:
        if hasattr(tr, "name") and isinstance(tr.name, str):
            tr.name = pt_label(tr.name)
        if hasattr(tr, "labels"):
            tr.labels = _normalize_seq(tr.labels)
        if hasattr(tr, "x"):
            tr.x = _normalize_seq(tr.x)
        if hasattr(tr, "y"):
            tr.y = _normalize_seq(tr.y)
        if tr.type == "bar":
            tr.cliponaxis = False


LAYOUT = dict(
    font=dict(family="Inter, Segoe UI, sans-serif", size=12, color="#1f2937"),
    margin=dict(l=90, r=40, t=95, b=120),
    title=dict(font=dict(size=16, color=COLORS["primary"]), x=0.5, xanchor="center"),
    colorway=COLORS["seq"],
    plot_bgcolor="white",
    paper_bgcolor="white",
    autosize=True,
    height=430,
    legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="center", x=0.5, title_text=""),
)


def fig_html(fig, div_id):
    fig.update_layout(**LAYOUT)
    apply_pt_formatting(fig)
    fig.update_xaxes(automargin=True)
    fig.update_yaxes(automargin=True)
    has_heatmap = False
    has_horizontal_bar = False
    has_pie = False
    for tr in fig.data:
        if tr.type == "bar" and getattr(tr, "orientation", None) == "h":
            has_horizontal_bar = True
        if tr.type == "heatmap":
            has_heatmap = True
        if tr.type == "pie":
            has_pie = True
    if has_pie:
        fig.update_layout(height=460, margin=dict(l=40, r=40, t=95, b=120))
    if has_heatmap:
        fig.update_layout(height=460, margin=dict(l=90, r=110, t=95, b=90))
    if has_horizontal_bar:
        fig.update_layout(height=520, margin=dict(l=170, r=60, t=95, b=110))
    return pio.to_html(fig, include_plotlyjs=False, full_html=False, div_id=div_id,
                       config={"displaylogo": False, "responsive": True})

# ================= FIGURAS =================
FIGS = {}

# --- Visão geral ---
f = go.Figure()
f.add_bar(x=ag_ano["ano_sinistro"], y=ag_ano["sinistros"], name="Sinistros",
          marker_color=COLORS["primary"], text=ag_ano["sinistros"], textposition="outside")
f.update_layout(title="Total de Sinistros por Ano (2014-2026)", xaxis_title="Ano", yaxis_title="Sinistros")
FIGS["sinistros_ano"] = f

f = go.Figure()
f.add_bar(x=ag_ano["ano_sinistro"], y=ag_ano["vitimas_fatais"], name="Óbitos",
          marker_color=COLORS["accent"], text=ag_ano["vitimas_fatais"], textposition="outside")
f.update_layout(title="Óbitos por Ano", xaxis_title="Ano", yaxis_title="Óbitos")
FIGS["obitos_ano"] = f

f = go.Figure()
for col, name, color in [("vitimas_fatais", "Fatais", COLORS["accent"]),
                          ("vitimas_graves", "Graves", COLORS["warn"]),
                          ("vitimas_leves", "Leves", COLORS["primary"])]:
    f.add_bar(x=ag_ano["ano_sinistro"], y=ag_ano[col], name=name, marker_color=color)
f.update_layout(barmode="stack", title="Vítimas por Gravidade (empilhado) — por Ano",
                xaxis_title="Ano", yaxis_title="Vítimas")
FIGS["vitimas_gravidade_ano"] = f

f = go.Figure(data=[go.Pie(labels=list(ag_modo.keys()), values=list(ag_modo.values()),
                           hole=.4, marker=dict(colors=COLORS["seq"]))])
f.update_layout(title="Modal / Tipo de Veículo Envolvido (participações)")
FIGS["modal"] = f

# --- Tipos de sinistro ---
top = ag_tp.head(10).sort_values("sinistros")
f = go.Figure()
f.add_bar(x=top["sinistros"], y=top["tp_sinistro_primario"], orientation="h",
         marker_color=COLORS["primary"], text=top["sinistros"], textposition="outside")
f.update_layout(title="Top 10 Tipos de Sinistro (2014-2026)", xaxis_title="Sinistros", yaxis_title="")
FIGS["tipos_sinistro"] = f

top2 = ag_tp.head(10)
f = go.Figure()
f.add_bar(x=top2["tp_sinistro_primario"], y=top2["fatais"], name="Óbitos",
         marker_color=COLORS["accent"])
f.add_bar(x=top2["tp_sinistro_primario"], y=top2["graves"], name="Feridos Graves",
         marker_color=COLORS["warn"])
f.update_layout(barmode="group", title="Gravidade por Tipo de Sinistro — Top 10",
                xaxis_title="", yaxis_title="Vítimas")
FIGS["tipos_gravidade"] = f

# --- Vítimas / demografia ---
grav = pd.DataFrame(ag_pes["gravidade"]).dropna()
f = go.Figure(data=[go.Pie(labels=grav["gravidade_lesao"], values=grav["n"], hole=.35,
                           marker=dict(colors=COLORS["seq"]))])
f.update_layout(title="Distribuição de Vítimas por Gravidade da Lesão")
FIGS["gravidade_lesao"] = f

sx = pd.DataFrame(ag_pes["sexo"]).dropna()
f = go.Figure(data=[go.Pie(labels=sx["sexo"], values=sx["n"], hole=.4,
                           marker=dict(colors=[COLORS["primary"], COLORS["accent"], COLORS["muted"]]))])
f.update_layout(title="Distribuição de Vítimas por Sexo")
FIGS["sexo"] = f

fe = pd.DataFrame(ag_pes["faixa_etaria"]).dropna()
fe = fe[fe["faixa_etaria_demografica"].str.contains("NAO DISPONIVEL") == False]
ordem_faixa = ["0 a 4", "5 a 9", "10 a 14", "15 a 19", "20 a 24", "25 a 29",
               "30 a 34", "35 a 39", "40 a 44", "45 a 49", "50 a 54", "55 a 59",
               "60 a 64", "65 a 69", "70 a 74", "75 a 79", "80 a 84", "85 ou mais"]
fe["ord"] = fe["faixa_etaria_demografica"].map({k: i for i, k in enumerate(ordem_faixa)})
fe = fe.sort_values("ord")
f = go.Figure()
f.add_bar(x=fe["faixa_etaria_demografica"], y=fe["n"], marker_color=COLORS["primary"])
f.update_layout(title="Vítimas por Faixa Etária", xaxis_title="Faixa etária", yaxis_title="Vítimas")
FIGS["faixa_etaria"] = f

tv = pd.DataFrame(ag_pes["tipo_vitima"]).dropna()
tv = tv.sort_values("n", ascending=True).tail(10)
f = go.Figure()
f.add_bar(x=tv["n"], y=tv["tipo_de_vitima"], orientation="h", marker_color=COLORS["accent"])
f.update_layout(title="Tipo de Vítima (Top 10)", xaxis_title="Vítimas", yaxis_title="")
FIGS["tipo_vitima"] = f

ob_ano = pd.DataFrame(ag_pes["obitos_por_ano"]).dropna()
f = go.Figure()
f.add_scatter(x=ob_ano["ano_sinistro"], y=ob_ano["n"], mode="lines+markers",
             line=dict(color=COLORS["accent"], width=3), marker=dict(size=9))
f.update_layout(title="Evolução de Óbitos por Ano (registro individual)", xaxis_title="Ano", yaxis_title="Óbitos")
FIGS["obitos_trend"] = f

tvi = pd.DataFrame(ag_pes["obitos_tipo_vitima"]).dropna().head(8)
f = go.Figure(data=[go.Pie(labels=tvi["tipo_de_vitima"], values=tvi["n"], hole=.35)])
f.update_layout(title="Óbitos por Tipo de Vítima")
FIGS["obitos_tipo"] = f

# --- Temporais ---
ag_mes["ym"] = ag_mes["ano_sinistro"].astype(str) + "-" + ag_mes["mes_sinistro"].astype(str).str.zfill(2)
ag_mes_s = ag_mes.sort_values(["ano_sinistro", "mes_sinistro"])
f = go.Figure()
f.add_scatter(x=ag_mes_s["ym"], y=ag_mes_s["sinistros"], mode="lines", name="Sinistros",
             line=dict(color=COLORS["primary"], width=2))
f.update_layout(title="Série Temporal Mensal — Sinistros", xaxis_title="Ano/Mês", yaxis_title="Sinistros")
FIGS["ts_mensal"] = f

pivot = ag_mes.pivot(index="mes_sinistro", columns="ano_sinistro", values="sinistros")
f = go.Figure(data=go.Heatmap(z=pivot.values, x=pivot.columns, y=pivot.index,
                              colorscale="Reds", colorbar=dict(title="Sinistros")))
f.update_layout(title="Sazonalidade — Sinistros (Mês × Ano)",
                xaxis_title="Ano", yaxis_title="Mês")
FIGS["heat_sazonalidade"] = f

f = go.Figure()
f.add_bar(x=ag_dia["dia_da_semana"], y=ag_dia["sinistros"], marker_color=COLORS["primary"])
f.update_layout(title="Sinistros por Dia da Semana", xaxis_title="Dia", yaxis_title="Sinistros")
FIGS["dia_semana"] = f

f = go.Figure()
f.add_bar(x=ag_dia["dia_da_semana"], y=ag_dia["fatais"], marker_color=COLORS["accent"])
f.update_layout(title="Óbitos por Dia da Semana", xaxis_title="Dia", yaxis_title="Óbitos")
FIGS["fatais_dia_semana"] = f

f = go.Figure()
f.add_bar(x=ag_turno["turno"], y=ag_turno["sinistros"], marker_color=COLORS["primary"], name="Sinistros")
f.add_bar(x=ag_turno["turno"], y=ag_turno["fatais"] * 20, marker_color=COLORS["accent"],
         name="Óbitos (×20)")
f.update_layout(title="Sinistros e Óbitos por Turno", barmode="group",
                xaxis_title="Turno", yaxis_title="Quantidade")
FIGS["turno"] = f

f = go.Figure()
f.add_bar(x=ag_hora["hora_num"], y=ag_hora["sinistros"], marker_color=COLORS["primary"], name="Sinistros")
f.add_scatter(x=ag_hora["hora_num"], y=ag_hora["fatais"] * 20, mode="lines+markers",
             line=dict(color=COLORS["accent"], width=3), name="Óbitos (×20)", yaxis="y")
f.update_layout(title="Distribuição Horária (0–23h)", xaxis_title="Hora do dia", yaxis_title="Quantidade")
FIGS["hora"] = f

# --- Geográfica (visões gerais) ---
rg = ag_reg.dropna().sort_values("sinistros", ascending=True).tail(15)
f = go.Figure()
f.add_bar(x=rg["sinistros"], y=rg["regiao_administrativa"], orientation="h",
         marker_color=COLORS["primary"])
f.update_layout(title="Sinistros por Região Administrativa (Top 15)",
                xaxis_title="Sinistros", yaxis_title="")
FIGS["regiao"] = f

rgf = ag_reg.dropna().sort_values("fatais", ascending=True).tail(15)
f = go.Figure()
f.add_bar(x=rgf["fatais"], y=rgf["regiao_administrativa"], orientation="h",
         marker_color=COLORS["accent"])
f.update_layout(title="Óbitos por Região Administrativa (Top 15)",
                xaxis_title="Óbitos", yaxis_title="")
FIGS["regiao_obitos"] = f

mn = ag_mun.dropna().head(20).sort_values("fatais", ascending=True)
f = go.Figure()
f.add_bar(x=mn["fatais"], y=mn["municipio"], orientation="h", marker_color=COLORS["accent"])
f.update_layout(title="Top 20 Municípios em Óbitos",
                xaxis_title="Óbitos", yaxis_title="")
FIGS["municipios_obitos"] = f

vm = ag_via.dropna().head(10).sort_values("sinistros", ascending=True)
f = go.Figure()
f.add_bar(x=vm["sinistros"], y=vm["tipo_via"], orientation="h", marker_color=COLORS["primary"])
f.update_layout(title="Sinistros por Tipo de Via", xaxis_title="Sinistros", yaxis_title="")
FIGS["tipo_via"] = f

adm = ag_adm.dropna()
f = go.Figure(data=[go.Pie(labels=adm["administracao"], values=adm["sinistros"], hole=.4)])
f.update_layout(title="Sinistros por Tipo de Administração da Via")
FIGS["administracao"] = f

# --- Padrões e correlações ---
# Heatmap Dia × Turno
sin = pd.read_parquet(OUT / "sinistros.parquet", columns=["dia_da_semana", "turno", "hora_num", "tem_fatal"])
hm = sin.pivot_table(index="turno", columns="dia_da_semana", values="hora_num",
                     aggfunc="count", fill_value=0)
dias_order = ["SEGUNDA-FEIRA", "TERCA-FEIRA", "QUARTA-FEIRA", "QUINTA-FEIRA",
              "SEXTA-FEIRA", "SABADO", "DOMINGO"]
hm = hm[[d for d in dias_order if d in hm.columns]]
turnos_order = ["MADRUGADA", "MANHA", "TARDE", "NOITE"]
hm = hm.reindex([t for t in turnos_order if t in hm.index])
f = go.Figure(data=go.Heatmap(z=hm.values, x=hm.columns, y=hm.index, colorscale="YlOrRd",
                              colorbar=dict(title="Sinistros")))
f.update_layout(title="Mapa de Calor — Dia da Semana × Turno", xaxis_title="", yaxis_title="Turno")
FIGS["heat_dia_turno"] = f

# Letalidade por hora
ag_hora["letalidade"] = ag_hora["fatais"] / ag_hora["sinistros"] * 100
f = go.Figure()
f.add_scatter(x=ag_hora["hora_num"], y=ag_hora["letalidade"], mode="lines+markers",
             line=dict(color=COLORS["accent"], width=3), marker=dict(size=9))
f.update_layout(title="Índice de Letalidade por Hora (% sinistros com óbito)",
                xaxis_title="Hora do dia", yaxis_title="% letalidade")
FIGS["letalidade_hora"] = f

# Tempo sinistro-óbito
to = ag_pes["tempo_obito_hist"]["values"]
tx = list(map(int, to.keys()))
ty = list(to.values())
order = sorted(range(len(tx)), key=lambda i: tx[i])
tx = [tx[i] for i in order]; ty = [ty[i] for i in order]
f = go.Figure()
f.add_bar(x=tx, y=ty, marker_color=COLORS["accent"])
f.update_layout(title="Tempo entre Sinistro e Óbito (dias) — 0 a 180",
                xaxis_title="Dias", yaxis_title="Óbitos")
FIGS["tempo_obito"] = f

# Evolução % vítimas por modo (usando pivot anos x modal aproximado)
# simples: linha de sinistros por ano vs óbitos por ano com razão
ag_ano["letalidade"] = ag_ano["vitimas_fatais"] / ag_ano["sinistros"] * 100
f = go.Figure()
f.add_scatter(x=ag_ano["ano_sinistro"], y=ag_ano["letalidade"], mode="lines+markers",
             line=dict(color=COLORS["accent"], width=3), name="Letalidade (%)")
f.update_layout(title="Índice Anual de Letalidade (% sinistros com óbito)",
                xaxis_title="Ano", yaxis_title="%")
FIGS["letalidade_ano"] = f

# ================= FIG GEOGRÁFICA — rodovias =================
def rod_bar(records, key, title, color):
    df = pd.DataFrame(records).sort_values(key, ascending=True)
    f = go.Figure()
    f.add_bar(x=df[key], y=df["Rodovia"], orientation="h", marker_color=color,
             text=df[key].round(2), textposition="outside")
    f.update_layout(title=title, xaxis_title=key, yaxis_title="")
    return f

FIGS["rod_top_sin"] = rod_bar(rod["top10_sinistros"], "sinistros",
                              "Top 10 Rodovias — Sinistros (2014-2026)", COLORS["primary"])
FIGS["rod_top_obi"] = rod_bar(rod["top10_obitos"], "obitos",
                              "Top 10 Rodovias — Óbitos", COLORS["accent"])
FIGS["rod_top_dens"] = rod_bar(rod["top10_densidade"], "sinistros_por_km",
                               "Top 10 Rodovias por Densidade (Sinistros/km) — ≥20km", COLORS["warn"])
FIGS["rod_top_let"] = rod_bar(rod["top10_letalidade"], "indice_letalidade",
                              "Top 10 Rodovias — Letalidade (%) — ≥100 sinistros", COLORS["accent"])
FIGS["rod_bottom_sin"] = rod_bar(rod["bottom10_sinistros"], "sinistros",
                                 "10 Rodovias com Menos Sinistros (≥5 eventos)", COLORS["ok"])

# Trechos
def trc_bar(records, key, title, color, labelcol="trecho_id"):
    df = pd.DataFrame(records).sort_values(key, ascending=True)
    df["label"] = df[labelcol].str.slice(0, 55)
    f = go.Figure()
    f.add_bar(x=df[key], y=df["label"], orientation="h", marker_color=color,
             text=df[key].round(2), textposition="outside")
    f.update_layout(title=title, xaxis_title=key, yaxis_title="", height=500)
    return f

FIGS["trc_top_sin"] = trc_bar(trc["top10_sinistros"], "sinistros",
                              "Top 10 Trechos (Subtrechos) — Sinistros", COLORS["primary"])
FIGS["trc_top_obi"] = trc_bar(trc["top10_obitos"], "obitos",
                              "Top 10 Trechos — Óbitos", COLORS["accent"])
FIGS["trc_top_dens"] = trc_bar(trc["top10_densidade"], "sinistros_por_km",
                               "Top 10 Trechos por Densidade (Sinistros/km)", COLORS["warn"])
FIGS["trc_top_ob_km"] = trc_bar(trc["top10_obitos_km"], "obitos_por_km",
                                "Top 10 Trechos por Óbitos/km", COLORS["accent"])

# Trechos da rodovia campeã
tc = trc["top10_trechos_rodovia_campea"]
FIGS["trc_campea"] = trc_bar(tc["trechos"], "sinistros",
                             f"Top 10 Trechos da Rodovia Campeã — {tc['rodovia']}",
                             COLORS["primary"])

# ================= TEMPLATE BASE =================
CSS = """
:root{--azul:#0e4d92;--vermelho:#d52b1e;--amarelo:#f7b500;--verde:#2e8b57;--bg:#f3f4f6;--ink:#1f2937;--muted:#6b7280;}
*{box-sizing:border-box}
body{margin:0;font-family:'Inter',Segoe UI,Arial,sans-serif;background:var(--bg);color:var(--ink);line-height:1.5}
header.hero{background:linear-gradient(135deg,#0e4d92 0%,#1e40af 60%,#d52b1e 140%);color:white;padding:48px 24px;text-align:center}
header.hero h1{margin:0 0 8px;font-size:2.2em;letter-spacing:.5px}
header.hero p{margin:4px 0;opacity:.95}
nav.top{background:#0b3a70;padding:10px 24px;display:flex;gap:12px;flex-wrap:wrap;justify-content:center;position:sticky;top:0;z-index:10}
nav.top a{color:#fff;text-decoration:none;padding:6px 14px;border-radius:6px;font-weight:500;font-size:.95em}
nav.top a:hover{background:#d52b1e}
nav.top i,section h2 i,.card h3 i{margin-right:6px}
main{width:90%;max-width:none;margin:0 5%;padding:28px 0 36px}
.kpis{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;margin:18px 0 0;width:100%}
.portal-kpis{grid-template-columns:repeat(3,minmax(0,1fr));max-width:none;margin:18px 0 0}
.kpi{background:linear-gradient(180deg,#ffffff 0%,#f8fbff 100%);padding:20px 16px;border-radius:16px;border:1px solid #dbe3ee;box-shadow:0 6px 18px rgba(15,23,42,.06);min-height:158px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}
.kpi .i{font-size:1.45rem;line-height:1;color:var(--azul);margin-bottom:10px}
.kpi .t{font-size:1rem;font-weight:700;color:#0f172a}
.kpi .v{margin-top:12px;font-size:2.02em;font-weight:800;color:var(--azul);line-height:1.1}
.kpi .l{margin-top:7px;color:var(--muted);font-size:.83em;letter-spacing:.1px}
.kpi.alert .i,.kpi.alert .v{color:var(--vermelho)}
.kpi.warn .i,.kpi.warn .v{color:#b88700}
.kpi.ok .i,.kpi.ok .v{color:var(--verde)}
section{background:white;margin:24px 0;padding:24px;border-radius:12px;box-shadow:0 2px 10px rgba(0,0,0,.05)}
section h2{color:var(--azul);margin-top:0;border-bottom:3px solid var(--vermelho);padding-bottom:8px;display:inline-block}
.section-intro{margin:2px 0 12px;color:var(--muted);max-width:980px}
.stats-shell,.filter-shell,.analytics-shell{background:linear-gradient(180deg,#ffffff 0%,#f8fbff 100%);border:1px solid #dbe3ee;border-radius:18px;box-shadow:0 6px 20px rgba(15,23,42,.05)}
section h3{color:var(--azul);margin-top:28px}
.dashboard-tabs{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0 6px}
.tab-btn{border:1px solid #cbd5e1;background:#fff;color:var(--azul);padding:10px 14px;border-radius:999px;font:inherit;font-weight:800;cursor:pointer;transition:.2s ease}
.tab-btn:hover{border-color:var(--azul);transform:translateY(-1px)}
.tab-btn.active{background:var(--azul);color:#fff;border-color:var(--azul);box-shadow:0 8px 18px rgba(14,77,146,.18)}
.tab-panel{display:none}
.tab-panel.active{display:block}
.chart-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px;margin-top:16px;align-items:start}
.demografia-grid .chart{min-height:490px}
.chart{background:#fafafa;padding:18px 18px 28px;border-radius:8px;border:1px solid #e5e7eb;overflow:hidden;min-width:0;min-height:460px}
.chart > div{width:100%!important;min-height:420px;max-width:100%!important}
.js-plotly-plot,.plot-container{width:100%!important;max-width:100%!important}
.gtitle{font-weight:700!important}
.card-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-top:16px;width:100%}
.card{background:white;border:1px solid #e5e7eb;border-radius:10px;padding:18px;box-shadow:0 1px 4px rgba(0,0,0,.05);transition:transform .2s,box-shadow .2s}
.card:hover{transform:translateY(-3px);box-shadow:0 6px 18px rgba(0,0,0,.1)}
.card h3{margin:0 0 8px;color:var(--azul);font-size:1.1em}
.card p{color:var(--muted);font-size:.9em}
.card a{display:inline-block;margin-top:10px;background:var(--azul);color:#fff;padding:8px 14px;border-radius:6px;text-decoration:none;font-size:.9em}
.card a:hover{background:var(--vermelho)}
.alert-box{background:#fff7ed;border-left:4px solid var(--amarelo);padding:12px 16px;margin:16px 0;border-radius:6px}
.insight{background:#eef4ff;border-left:4px solid var(--azul);padding:12px 16px;margin:16px 0;border-radius:6px}
.danger{background:#fef2f2;border-left:4px solid var(--vermelho);padding:12px 16px;margin:16px 0;border-radius:6px}
table.tbl{width:100%;border-collapse:collapse;margin-top:12px;font-size:.92em}
table.tbl th,table.tbl td{padding:8px 10px;border-bottom:1px solid #e5e7eb;text-align:left}
table.tbl thead{background:var(--azul);color:white}
table.tbl tr:nth-child(even){background:#f9fafb}
footer{background:#0b3a70;color:#cbd5e1;padding:24px;text-align:center;margin-top:40px}
footer a{color:#fff;text-decoration:none}
#map,#mapSub{height:720px;border-radius:14px;border:1px solid #dbe3ee}
.legend-map{background:white;padding:10px 12px;border-radius:8px;box-shadow:0 6px 18px rgba(0,0,0,.16);font-size:.85em;line-height:1.55;max-width:260px}
.legend-map .sw{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:6px;vertical-align:middle}
.layer-sidebar{background:rgba(255,255,255,.96);padding:10px 12px;border-radius:10px;box-shadow:0 8px 24px rgba(15,23,42,.18);min-width:240px;max-width:280px;font-size:.84em;line-height:1.45;border:1px solid #dbe3ee}
.layer-sidebar h4{margin:0 0 8px;color:var(--azul);font-size:.95em}
.layer-group{border-top:1px solid #e5e7eb;padding-top:8px;margin-top:8px}
.layer-group:first-of-type{border-top:none;padding-top:0;margin-top:0}
.layer-group .master{font-weight:700;color:#0b3a70;display:flex;gap:8px;align-items:center}
.layer-items{padding-left:20px;margin-top:6px;display:grid;gap:4px}
.layer-items label{display:flex;gap:8px;align-items:center;color:#334155}
.sym-marker span{display:inline-flex;align-items:center;justify-content:center;font-weight:800;text-shadow:0 1px 1px rgba(255,255,255,.6)}
.sym-marker.point span{font-size:16px}
.sym-marker.micro span{font-size:11px}
.pill{display:inline-block;padding:2px 10px;border-radius:999px;background:#eef4ff;color:var(--azul);font-size:.8em;margin-right:4px}
.geo-main{width:90%;max-width:none;margin:0 5%;padding:20px 0 32px}
.filter-shell,.stats-shell,.analytics-shell{margin:20px 0;padding:22px 24px}
.filters{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:16px;align-items:end;margin-top:14px}
.filters label{display:flex;flex-direction:column;gap:7px;font-weight:600;color:var(--azul);font-size:.92em}
.filters select,.filters input,.filters button{border:1px solid #cbd5e1;border-radius:10px;padding:11px 12px;font:inherit;background:white;color:var(--ink)}
.filters input[type="range"]{padding:0}
.filters button{background:var(--azul);color:white;font-weight:700;cursor:pointer;min-height:44px;align-self:end}
.filters button:hover{background:#0b3a70}
.checkline{display:flex;gap:14px;align-items:center;flex-wrap:wrap;padding-top:10px}
.checkline label{display:flex;flex-direction:row;align-items:center;gap:8px;font-weight:500;color:var(--ink)}
.geo-board{display:grid;grid-template-columns:minmax(700px,1.45fr) minmax(420px,1fr);gap:20px;margin-top:10px;align-items:start;padding:20px;border-radius:20px;background:linear-gradient(180deg,#eef5ff 0%,#f8fbff 100%);box-shadow:0 10px 28px rgba(15,23,42,.08);border:1px solid #dbe3ee}
.geo-board-inline{grid-template-columns:1fr}
.geo-rail{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;align-content:start}
.geo-rail-five{grid-template-columns:repeat(2,minmax(260px,1fr));align-items:stretch}
.geo-rail-five .span-2{grid-column:1 / -1}
.geo-panel{background:white;padding:18px;border-radius:16px;box-shadow:0 4px 16px rgba(15,23,42,.06);border:1px solid #dbe3ee;min-width:0}
.geo-panel.map-panel{position:sticky;top:76px}
.map-composite{display:grid;grid-template-columns:minmax(640px,1.2fr) minmax(480px,1fr);gap:18px;align-items:stretch}
.map-stage{display:flex;flex-direction:column;gap:10px;height:100%}
.map-stage #map,.map-stage #mapSub{flex:1 1 auto;height:100%;min-height:860px}
.geo-rail .geo-panel h2{font-size:1em;margin-bottom:10px}
.plot-host{width:100%;min-height:280px}
.plot-timeline{min-height:320px;margin-top:8px}
.layer-hint{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}
.layer-chip{display:inline-flex;align-items:center;gap:6px;padding:5px 10px;border-radius:999px;background:#eef4ff;color:var(--azul);font-size:.82em;font-weight:600}
.map-tip{background:#f8fafc;border:1px solid #e5e7eb;border-radius:12px;padding:11px 13px;margin-top:14px;color:var(--muted);font-size:.9em}
.leaflet-control-layers{border:none!important;box-shadow:0 8px 24px rgba(15,23,42,.18)!important;border-radius:10px!important}
.leaflet-control-layers-expanded{padding:10px 12px;background:white}
.leaflet-popup-content{line-height:1.45}
.small-note{color:var(--muted);font-size:.92em;margin-top:6px}
@media (max-width: 1100px){
  main,.geo-main{padding:16px}
  .kpis,.portal-kpis,.card-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
  .chart-grid{grid-template-columns:1fr}
  .chart{min-height:400px}
  .chart > div{min-height:360px}
  .filter-shell,.stats-shell,.analytics-shell{padding:16px}
  .geo-board{grid-template-columns:1fr;padding:12px}
  .geo-rail,.geo-rail-five{grid-template-columns:1fr}
  .geo-rail-five .span-2{grid-column:auto}
  .map-composite{grid-template-columns:1fr}
  .geo-panel.map-panel{position:static}
  #map,#mapSub{height:560px}
  .map-stage #map{min-height:560px}
}
@media (max-width: 680px){
  .kpis,.portal-kpis,.card-grid{grid-template-columns:1fr}
}
"""

NAV = """
<nav class="top">
  <a href="index.html"><i class="fa-solid fa-house"></i> Portal</a>
  <a href="dashboard_principal.html"><i class="fa-solid fa-chart-column"></i> Dashboard</a>
  <a href="analise_geografica.html"><i class="fa-solid fa-road"></i> Dash Rodovias</a>
  <a href="analise_subtrechos.html"><i class="fa-solid fa-route"></i> Dash Subtrechos</a>
  <a href="RELATORIO_EXECUTIVO.html"><i class="fa-solid fa-file-lines"></i> Relatório Executivo</a>
  <a href="GUIA_ACESSO.html"><i class="fa-solid fa-book"></i> Guia</a>
</nav>
"""

FOOTER = f"""
<footer>
  <div>Infosiga SP · Detran SP · Análise Exploratória de Sinistros (2014 – 2026)</div>
  <div>Fontes: <a href="https://infosiga.detran.sp.gov.br">infosiga.detran.sp.gov.br</a> · Malha Rodoviária DER/SP</div>
  <div style="margin-top:6px;color:#94a3b8;font-size:.85em">© 2026 — Gerado em {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}</div>
</footer>
"""

def html_page(title, body, extra_head=""):
    return f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js" charset="utf-8"></script>
<style>{CSS}</style>
{extra_head}
</head>
<body>
{NAV}
{body}
{FOOTER}
</body></html>"""

# ============ PORTAL ============
kpi_html = f"""
<div class="kpis portal-kpis">
  <div class="kpi">
    <div class="i"><i class="fa-solid fa-car-burst"></i></div>
    <div class="t">Sinistros</div>
    <div class="v">{br(kpi['total_sinistros'])}</div>
  </div>
  <div class="kpi alert">
    <div class="i"><i class="fa-solid fa-crosshairs"></i></div>
    <div class="t">Óbitos</div>
    <div class="v">{br(kpi['total_obitos'])}</div>
  </div>
  <div class="kpi warn">
    <div class="i"><i class="fa-solid fa-triangle-exclamation"></i></div>
    <div class="t">Feridos graves</div>
    <div class="v">{br(kpi['total_graves'])}</div>
  </div>
  <div class="kpi">
    <div class="i"><i class="fa-solid fa-kit-medical"></i></div>
    <div class="t">Feridos leves</div>
    <div class="v">{br(kpi['total_leves'])}</div>
  </div>
  <div class="kpi">
    <div class="i"><i class="fa-solid fa-people-group"></i></div>
    <div class="t">Pessoas envolvidas</div>
    <div class="v">{br(kpi['total_pessoas'])}</div>
  </div>
  <div class="kpi ok">
    <div class="i"><i class="fa-solid fa-map-location-dot"></i></div>
    <div class="t">Com geolocalização</div>
    <div class="v">{pct(kpi['perc_com_coord'])}%</div>
  </div>
</div>
"""

cards_html = """
<div class="card-grid">
  <div class="card">
    <h3><i class="fa-solid fa-chart-column"></i> Dashboard Interativo</h3>
    <p>Todos os gráficos organizados em cinco categorias temáticas: Visão Geral, Vítimas &amp; Demografia, Séries Temporais, Geográfica e Padrões.</p>
    <a href="dashboard_principal.html">Acessar Dashboard</a>
  </div>
  <div class="card">
    <h3><i class="fa-solid fa-road"></i> Dashboard de Rodovias</h3>
    <p>Visão tática por rodovia, tipo de evento e ano, aproveitando a malha completa do DER/SP no mapa interativo.</p>
    <a href="analise_geografica.html">Abrir Dashboard 1</a>
  </div>
  <div class="card">
    <h3><i class="fa-solid fa-route"></i> Dashboard de Subtrechos</h3>
    <p>Visão detalhada por subtrecho, tipo de evento e ano, focada nas top 10 rodovias de cada tipologia de sinistro.</p>
    <a href="analise_subtrechos.html">Abrir Dashboard 2</a>
  </div>
  <div class="card">
    <h3><i class="fa-solid fa-file-lines"></i> Relatório Executivo</h3>
    <p>Visão analítica consolidada, com principais achados, contextualização do Infosiga, ressalvas metodológicas e recomendações.</p>
    <a href="RELATORIO_EXECUTIVO.html">Ler Relatório</a>
  </div>
  <div class="card">
    <h3><i class="fa-solid fa-book"></i> Guia de Acesso</h3>
    <p>Lista de todos os gráficos, descrição das análises e navegação rápida entre as páginas.</p>
    <a href="GUIA_ACESSO.html">Ver Guia</a>
  </div>
</div>
"""

anos_range = f"{kpi['ano_min']} – {kpi['ano_max']}"
portal_body = f"""
<header class="hero">
  <h1>Análise de Acidentes Rodoviários — Infosiga SP</h1>
  <p>Análise Exploratória Completa — Estado de São Paulo · {anos_range}</p>
  <p style="font-size:.9em;opacity:.85">Base oficial Detran SP · Malha Rodoviária DER/SP</p>
</header>
<main>
{kpi_html}
<section>
  <h2>Sobre esta análise</h2>
  <p>Esta análise integra a base pública <strong>Infosiga SP</strong> (sinistros, vítimas e veículos, 2014–2026) à
  <strong>Malha Rodoviária Estadual</strong> do DER/SP, caracterizando padrões temporais, demográficos, modais e geográficos
  dos sinistros de trânsito no estado de São Paulo. Todos os gráficos são interativos (Plotly) e o mapa é navegável (Leaflet).</p>
  <div class="insight"><strong>Contextualização do Infosiga:</strong> o Infosiga é o sistema oficial de integração
  de dados de sinistros de trânsito do Estado de São Paulo, mantido pelo Detran-SP com contribuição da ARTESP, do DER,
  das Polícias Civil, Militar e Rodoviária Federal, e da Fundação Seade. O sistema consolida três visões (sinistro,
  vítima e veículo) e alimenta o painel público
  (<a href="https://infosiga.detran.sp.gov.br">infosiga.detran.sp.gov.br</a>). <strong>Ressalva:</strong> os registros
  possuem caráter notificacional; dados recentes (≤ 90 dias) são preliminares; a geolocalização é derivada dos
  boletins e apresenta cobertura de {pct(kpi['perc_com_coord'])}% neste conjunto.</div>
</section>
<section>
  <h2>Recursos Disponíveis</h2>
  {cards_html}
</section>
<section>
  <h2>Indicadores-chave (todo o período)</h2>
  <ul>
    <li><strong>Sinistros registrados:</strong> {br(kpi['total_sinistros'])}</li>
    <li><strong>Sinistros com vítima:</strong> {br(kpi['total_sinistros_com_vitima'])} ({pct(kpi['total_sinistros_com_vitima']/kpi['total_sinistros']*100)}%)</li>
    <li><strong>Sinistros fatais:</strong> {br(kpi['total_sinistros_fatais'])} ({pct(kpi['total_sinistros_fatais']/kpi['total_sinistros']*100, 2)}%)</li>
    <li><strong>Óbitos:</strong> {br(kpi['total_obitos'])} · <strong>Graves:</strong> {br(kpi['total_graves'])}</li>
    <li><strong>Em rodovias:</strong> {pct(kpi['perc_em_rodovia'])}% dos sinistros</li>
  </ul>
</section>
</main>
"""
(DOCS / "index.html").write_text(html_page("Infosiga SP — Portal", portal_body), encoding="utf-8")

# ============ DASHBOARD ============
def section(titulo, chaves, extra_class=""):
    charts = "\n".join(f'<div class="chart">{fig_html(FIGS[k], f"chart_{k}")}</div>' for k in chaves)
    classes = f"chart-grid {extra_class}".strip()
    return f"""<section><h2>{titulo}</h2><div class="{classes}">{charts}</div></section>"""


def dashboard_tabs():
    tabs = [
        ("tab_visao", '<i class="fa-solid fa-thumbtack"></i> Visão Geral', ["sinistros_ano", "obitos_ano", "vitimas_gravidade_ano", "modal", "tipos_sinistro", "tipos_gravidade"], ""),
        ("tab_demografia", '<i class="fa-solid fa-people-group"></i> Análise de Vítimas & Demografia', ["gravidade_lesao", "sexo", "faixa_etaria", "tipo_vitima", "obitos_trend", "obitos_tipo"], "demografia-grid"),
        ("tab_temporal", '<i class="fa-solid fa-clock"></i> Séries Temporais & Sazonalidade', ["ts_mensal", "heat_sazonalidade", "dia_semana", "fatais_dia_semana", "turno", "hora"], ""),
        ("tab_geo", '<i class="fa-solid fa-map-location-dot"></i> Análise Geográfica (agregada)', ["regiao", "regiao_obitos", "municipios_obitos", "tipo_via", "administracao"], ""),
        ("tab_padroes", '<i class="fa-solid fa-puzzle-piece"></i> Padrões & Correlações', ["heat_dia_turno", "letalidade_hora", "letalidade_ano", "tempo_obito"], ""),
    ]
    buttons = "\n".join(
        f'<button class="tab-btn{" active" if i == 0 else ""}" data-tab="{tab_id}">{label}</button>'
        for i, (tab_id, label, _, _) in enumerate(tabs)
    )

    panel_blocks = []
    for i, (tab_id, label, keys, extra_class) in enumerate(tabs):
        panel_content = section(label, keys, extra_class)
        if i == 0:
            panel_blocks.append(f'<div class="tab-panel active" id="{tab_id}" data-loaded="true">{panel_content}</div>')
        else:
            panel_blocks.append(
                f'<div class="tab-panel" id="{tab_id}" data-loaded="false"><div class="small-note">Abra esta aba para carregar os gráficos.</div></div>'
                f'<template id="tpl_{tab_id}">{panel_content}</template>'
            )
    panels = "\n".join(panel_blocks)

    script = """
<script>
(function () {
  const buttons = Array.from(document.querySelectorAll('.tab-btn'));
  const panels = Array.from(document.querySelectorAll('.tab-panel'));

  function executeScripts(container) {
    container.querySelectorAll('script').forEach((oldScript) => {
      const newScript = document.createElement('script');
      Array.from(oldScript.attributes).forEach((attr) => newScript.setAttribute(attr.name, attr.value));
      newScript.text = oldScript.textContent;
      oldScript.parentNode.replaceChild(newScript, oldScript);
    });
  }

  function ensureLoaded(panel) {
    if (!panel || panel.dataset.loaded === 'true') return;
    const template = document.getElementById(`tpl_${panel.id}`);
    if (!template) return;
    panel.innerHTML = template.innerHTML;
    panel.dataset.loaded = 'true';
    executeScripts(panel);
  }

  function resizePanel(panel) {
    if (!panel || !window.Plotly) return;
    panel.querySelectorAll('.js-plotly-plot').forEach((plot) => {
      try { Plotly.Plots.resize(plot); } catch (e) {}
    });
  }

  function activateTab(targetId) {
    buttons.forEach((b) => b.classList.toggle('active', b.dataset.tab === targetId));
    panels.forEach((panel) => {
      const isActive = panel.id === targetId;
      panel.classList.toggle('active', isActive);
      if (isActive) {
        ensureLoaded(panel);
        setTimeout(() => resizePanel(panel), 80);
      }
    });
  }

  buttons.forEach((btn) => {
    btn.addEventListener('click', () => activateTab(btn.dataset.tab));
  });

  window.addEventListener('load', () => activateTab((document.querySelector('.tab-btn.active') || buttons[0]).dataset.tab));
  window.addEventListener('resize', () => resizePanel(document.querySelector('.tab-panel.active')));
})();
</script>
"""
    return f"""
<section>
  <h2>Painéis Temáticos</h2>
  <p class="section-intro">Cada tema do dashboard agora está separado em uma aba dedicada, com carregamento sob demanda para deixar a página mais rápida.</p>
  <div class="dashboard-tabs">{buttons}</div>
  {panels}
</section>
{script}
"""


dash_body = f"""
<header class="hero">
  <h1>Dashboard Interativo — Infosiga SP</h1>
  <p>Análise completa {anos_range} · {br(kpi['total_sinistros'])} sinistros · {br(kpi['total_obitos'])} óbitos</p>
</header>
<main>
{kpi_html}
{dashboard_tabs()}
</main>
"""
(DOCS / "dashboard_principal.html").write_text(html_page("Dashboard Infosiga SP", dash_body), encoding="utf-8")

# ============ RELATÓRIO EXECUTIVO ============
# Rankings em tabelas
def records_to_table(records, cols, headers, round_cols=None):
    round_cols = round_cols or {}
    rows = []
    for r_ in records:
        cells = []
        for c in cols:
            v = r_.get(c)
            if v is None:
                cells.append("—")
            elif c in round_cols:
                try: cells.append(f"{float(v):,.{round_cols[c]}f}".replace(",", "X").replace(".", ",").replace("X", "."))
                except: cells.append(str(v))
            elif isinstance(v, (int, float)) and not isinstance(v, bool):
                cells.append(f"{v:,.0f}".replace(",", "."))
            else:
                cells.append(str(v))
        rows.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
    head = "<tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>"
    return f"<table class='tbl'><thead>{head}</thead><tbody>{''.join(rows)}</tbody></table>"

ano_max = int(ag_ano["ano_sinistro"].max())
ano_prev = ano_max - 1
sin_now = int(ag_ano[ag_ano["ano_sinistro"] == ano_max]["sinistros"].iloc[0])
sin_prev = int(ag_ano[ag_ano["ano_sinistro"] == ano_prev]["sinistros"].iloc[0])
var_sin = (sin_now - sin_prev) / sin_prev * 100 if sin_prev else 0
obi_now = int(ag_ano[ag_ano["ano_sinistro"] == ano_max]["vitimas_fatais"].iloc[0])
obi_prev = int(ag_ano[ag_ano["ano_sinistro"] == ano_prev]["vitimas_fatais"].iloc[0])
var_obi = (obi_now - obi_prev) / obi_prev * 100 if obi_prev else 0

pior_rod = rod["top10_obitos"][0]
pior_trc = trc["top10_obitos"][0]

rel_body = f"""
<header class="hero">
  <h1>Relatório Executivo — Infosiga SP</h1>
  <p>Análise Exploratória de Sinistros Rodoviários · Estado de SP · {anos_range}</p>
</header>
<main>

<section>
  <h2>Resumo Executivo</h2>
  {kpi_html}
  <p>O presente relatório consolida a análise exploratória da base <strong>Infosiga SP</strong>, abrangendo
  {br(kpi['total_sinistros'])} sinistros registrados entre {kpi['ano_min']} e {kpi['ano_max']},
  {br(kpi['total_pessoas'])} pessoas envolvidas e {br(kpi['total_obitos'])} óbitos computados pelo sistema.
  A base foi cruzada espacialmente com a <strong>Malha Rodoviária Estadual do DER/SP</strong> (4.782 trechos),
  permitindo ranquear rodovias e subtrechos segundo diferentes indicadores de risco.</p>

  <div class="alert-box">
  <strong>Ressalvas metodológicas:</strong>
  <ul>
    <li>A base Infosiga agrega notificações de múltiplas fontes (Polícia Militar, Polícia Civil, PRF, DER, ARTESP e SAMU/Seade); os dados dos últimos 90 dias são preliminares.</li>
    <li>{kpi['perc_com_coord']:.1f}% dos sinistros possuem coordenadas válidas; a análise geográfica por rodovia considera apenas os eventos associados a um trecho da Malha DER até 300 m de distância.</li>
    <li>A classificação “em rodovia” utiliza os campos <code>tipo_via</code> e <code>administracao</code>; sinistros marcados como “NÃO DISPONÍVEL” foram tratados de forma conservadora.</li>
    <li>Os totais de óbitos podem divergir do painel público do Infosiga em função do critério temporal adotado (data do sinistro x data do óbito, até 30 dias).</li>
  </ul>
  </div>
</section>

<section>
  <h2>Tendências Anuais</h2>
  <div class="chart">{fig_html(FIGS["sinistros_ano"], "rel_sin_ano")}</div>
  <div class="chart">{fig_html(FIGS["obitos_ano"], "rel_obi_ano")}</div>
  <div class="insight">
    <strong>Variação {ano_prev} → {ano_max}:</strong>
    Sinistros: {var_sin:+.1f}% &nbsp; · &nbsp; Óbitos: {var_obi:+.1f}%.
    Observação: o ano mais recente pode incluir dados parciais.
  </div>
</section>

<section>
  <h2>Perfil das Vítimas</h2>
  <div class="chart-grid">
    <div class="chart">{fig_html(FIGS["gravidade_lesao"], "rel_grav")}</div>
    <div class="chart">{fig_html(FIGS["tipo_vitima"], "rel_tv")}</div>
    <div class="chart">{fig_html(FIGS["faixa_etaria"], "rel_fx")}</div>
    <div class="chart">{fig_html(FIGS["obitos_tipo"], "rel_obtv")}</div>
  </div>
  <div class="insight"><strong>Destaques:</strong> motociclistas e pedestres concentram as maiores parcelas
  de óbitos, reafirmando o padrão de vulnerabilidade dos “usuários desprotegidos da via” (Plano Vida no
  Trânsito / Infosiga).</div>
</section>

<section>
  <h2>Padrões Temporais</h2>
  <div class="chart-grid">
    <div class="chart">{fig_html(FIGS["heat_sazonalidade"], "rel_haz")}</div>
    <div class="chart">{fig_html(FIGS["heat_dia_turno"], "rel_hdt")}</div>
    <div class="chart">{fig_html(FIGS["hora"], "rel_hora")}</div>
    <div class="chart">{fig_html(FIGS["letalidade_hora"], "rel_leth")}</div>
  </div>
  <div class="insight"><strong>Letalidade horária:</strong> embora o volume de sinistros se concentre no
  período comercial e no fim de tarde, o índice de letalidade (percentual de sinistros com óbito) é
  sistematicamente maior na madrugada, compatível com velocidades médias mais altas, fadiga e maior
  presença de álcool.</div>
</section>

<section>
  <h2>Rodovias Críticas (DER/SP)</h2>
  <p>Cruzamento de <strong>{br(kpi['total_sinistros'])}</strong> sinistros com a <strong>Malha DER/SP</strong> —
  {len(rod['all'])} rodovias estaduais com eventos associados.</p>

  <h3>Top 10 por óbitos</h3>
  {records_to_table(rod["top10_obitos"], ["Rodovia","sinistros","obitos","graves","km_total","sinistros_por_km","indice_letalidade"],
                    ["Rodovia","Sinistros","Óbitos","Graves","Extensão (km)","Sinistros/km","Letalidade %"],
                    round_cols={"km_total":1,"sinistros_por_km":2,"indice_letalidade":2})}

  <h3>Top 10 por densidade (sinistros/km — mín. 20 km)</h3>
  {records_to_table(rod["top10_densidade"], ["Rodovia","sinistros","km_total","sinistros_por_km","obitos"],
                    ["Rodovia","Sinistros","Extensão (km)","Sinistros/km","Óbitos"],
                    round_cols={"km_total":1,"sinistros_por_km":2})}

  <div class="danger"><strong>Rodovia crítica:</strong> {pior_rod['Rodovia']} com
  {br(pior_rod['obitos'])} óbitos acumulados no período.</div>

  <h3>Top 10 trechos por óbitos</h3>
  {records_to_table(trc["top10_obitos"], ["Rodovia","trecho_id","Extensao","sinistros","obitos","obitos_por_km"],
                    ["Rodovia","Subtrecho (DER)","Ext. (km)","Sinistros","Óbitos","Óbitos/km"],
                    round_cols={"Extensao":2,"obitos_por_km":3})}
  <div class="danger"><strong>Trecho mais letal:</strong> {pior_trc['trecho_id']} —
  {br(pior_trc['obitos'])} óbitos em {float(pior_trc.get('Extensao',0)):.2f} km.</div>
</section>

<section>
  <h2>Recomendações</h2>
  <ul>
    <li>Priorizar fiscalização ostensiva e engenharia viária nos <strong>dez trechos mais letais</strong>; pontos de concentração espacial oferecem melhor relação custo-benefício do que medidas genéricas.</li>
    <li>Intensificar operações nas faixas horárias de maior letalidade (madrugada) e nos meses com pico sazonal (ver mapa de calor).</li>
    <li>Implementar ações de proteção a usuários vulneráveis (motociclistas, pedestres e ciclistas), responsáveis por parcela desproporcional dos óbitos.</li>
    <li>Revisar trechos com densidade anômala (sinistros/km acima da média), mesmo quando o volume absoluto for moderado.</li>
    <li>Aprimorar a geolocalização dos registros (atualmente em {kpi['perc_com_coord']:.1f}%) para viabilizar análises em nível de micropontos, alinhadas ao Infomapa do Infosiga.</li>
  </ul>
</section>
</main>
"""
(DOCS / "RELATORIO_EXECUTIVO.html").write_text(html_page("Relatório Executivo — Infosiga SP", rel_body), encoding="utf-8")

# ============ ANÁLISE GEOGRÁFICA (dashboard interativo com Leaflet + Plotly) ============
malha_obj = json.load(open(OUT / "malha_topN.geojson", encoding="utf-8"))
road_names_geo = sorted({f_["properties"]["Rodovia"] for f_ in malha_obj["features"]})
road_rows_geo = [r_ for r_ in rod["all"] if r_["Rodovia"] in road_names_geo]

geo_asset_path = write_json_asset("geo/rodovias_dashboard_main.json", {
    "roadRowsAll": road_rows_geo,
    "roadRowsByYear": rod.get("all_by_year", []),
    "roadRowsByYearType": rod.get("all_by_year_type", []),
    "malha": malha_obj,
})
geo_analytics_asset_path = write_json_asset("geo/rodovias_dashboard_analytics.json", {
    "annualRows": ag_ano[["ano_sinistro", "sinistros", "vitimas_fatais"]].to_dict(orient="records"),
    "monthlyRows": ag_mes[["ano_sinistro", "mes_sinistro", "sinistros", "fatais"]].to_dict(orient="records"),
    "segRowsByYear": trc.get("all_by_year", []),
    "segRowsByType": trc.get("all_by_type", []),
    "segRowsByYearType": trc.get("all_by_year_type", []),
})
geo_overlay_asset_path = write_json_asset("geo/rodovias_dashboard_overlays.json", {
    "obitosPts": json.load(open(OUT / "pontos_obitos.geojson", encoding="utf-8")),
    "sinistrosPts": json.load(open(OUT / "pontos_sinistros_amostra.geojson", encoding="utf-8")),
    "pontosTipos": json.load(open(OUT / "pontos_vitimas_amostra.geojson", encoding="utf-8")),
    "heatSinistros": json.load(open(OUT / "heat_points_sinistros.json", encoding="utf-8")),
    "heatObitos": json.load(open(OUT / "heat_points_obitos.json", encoding="utf-8")),
})
year_options_html = "\n".join(f'<option value="{int(a)}">{int(a)}</option>' for a in ag_ano["ano_sinistro"].tolist())

geo_head = """
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdn.jsdelivr.net/npm/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>
"""

geo_body = f"""
<header class="hero">
  <h1>Dashboard 1 — Análise por Rodovias</h1>
  <p>Cruzamento Infosiga × Malha DER/SP · leitura por rodovia, tipo de evento e ano · com apoio da malha completa</p>
</header>
<main class="geo-main">
<section class="stats-shell">
  <h2>Estatística</h2>
  <p class="section-intro">Resumo consolidado do recorte geográfico ativo, sempre alinhado aos filtros analíticos.</p>
  <div id="geo-kpis" class="kpis"></div>
</section>

<section class="filter-shell">
  <h2>Filtros analíticos</h2>
  <p class="section-intro">Escolha primeiro o indicador, depois o tipo do evento, o período e por fim a rodovia para sincronizar todo o painel.</p>
  <div class="filters">
    <label>Indicador
      <select id="fltMetric">
        <option value="" disabled selected>Selecione um valor...</option>
        <option value="sinistros">Sinistros</option>
        <option value="obitos">Óbitos</option>
        <option value="sinistros_por_km">Sinistros por km</option>
        <option value="indice_letalidade">Letalidade (%)</option>
      </select>
    </label>
    <label>Tipo do evento
      <select id="fltEventType">
        <option value="" disabled selected>Selecione um valor...</option>
        <option value="ALL">Todos</option>
        <option value="COLISAO">Colisão</option>
        <option value="CHOQUE">Choque</option>
        <option value="ATROPELAMENTO">Atropelamento</option>
        <option value="OUTROS">Outros / não informado</option>
      </select>
    </label>
    <label>Período
      <select id="fltYear">
        <option value="" disabled selected>Selecione um valor...</option>
        <option value="ALL">Todos os períodos ({anos_range})</option>
        {year_options_html}
      </select>
    </label>
    <label>Rodovias
      <select id="fltRoad">
        <option value="" disabled selected>Selecione um valor...</option>
        <option value="ALL">Todas as rodovias do mapa</option>
      </select>
    </label>
    <label>Ordenação
      <select id="fltOrder">
        <option value="" disabled selected>Selecione um valor...</option>
        <option value="desc">Maiores valores</option>
        <option value="asc">Menores valores</option>
      </select>
    </label>
    <label>Top N exibido
      <input id="fltTopN" type="range" min="4" max="12" step="1" value="8" />
    </label>
    <button id="btnReset" type="button">Limpar seleção</button>
  </div>
  <div class="checkline">
    <span id="topNLabel" class="small-note">Exibindo Top 8 · O checkbox do grupo controla todas as camadas internas do Leaflet.</span>
  </div>
  <div class="layer-hint">
    <span class="layer-chip">Período analisado: {anos_range}</span>
    <span class="layer-chip">Mapa e gráficos 100% sincronizados</span>
    <span class="layer-chip">Cores e símbolos por categoria</span>
  </div>
</section>

<section class="analytics-shell">
  <h2>Painel analítico</h2>
  <p id="map-caption" class="section-intro">Mapa e gráficos lado a lado, com resposta cruzada a todos os filtros do painel.</p>
  <div class="geo-board geo-board-inline">
    <section class="geo-panel map-panel">
      <div class="map-composite">
        <div class="map-stage">
          <h2><i class="fa-solid fa-map-location-dot"></i> Mapa DER com camadas</h2>
          <div id="map"></div>
          <div class="layer-hint">
            <span class="layer-chip">Trechos DER por criticidade</span>
            <span class="layer-chip">Eventos por tipo</span>
            <span class="layer-chip">Pontos fatais</span>
            <span class="layer-chip">Mapa de calor</span>
          </div>
          <div class="map-tip">Os grupos da barra lateral do mapa ligam ou desligam automaticamente todas as camadas internas.</div>
        </div>

        <div class="geo-rail geo-rail-five">
          <section class="geo-panel">
            <h2><i class="fa-solid fa-trophy"></i> Ranking de rodovias</h2>
            <div id="roadRankChart" class="plot-host"></div>
          </section>

          <section class="geo-panel">
            <h2><i class="fa-solid fa-circle-notch"></i> Participação no indicador</h2>
            <div id="bubbleChart" class="plot-host"></div>
          </section>

          <section class="geo-panel">
            <h2><i class="fa-solid fa-route"></i> Subtrechos da rodovia selecionada</h2>
            <div id="segmentChart" class="plot-host"></div>
          </section>

          <section class="geo-panel">
            <h2><i class="fa-solid fa-chart-pie"></i> Composição do risco</h2>
            <div id="compareChart" class="plot-host"></div>
          </section>

          <section class="geo-panel span-2">
            <h2><i class="fa-solid fa-clock"></i> Leitura temporal integrada</h2>
            <div id="timelineChart" class="plot-host plot-timeline"></div>
          </section>
        </div>
      </div>
    </section>
  </div>
</section>
</main>
<script>
const GEO_DATA_URL = '{geo_asset_path}';
const GEO_ANALYTICS_URL = '{geo_analytics_asset_path}';
const GEO_OVERLAY_URL = '{geo_overlay_asset_path}';
let roadRowsAll = [];
let roadRowsByYear = [];
let roadRowsByYearType = [];
let annualRows = [];
let monthlyRows = [];
let malha = {{ type: 'FeatureCollection', features: [] }};
let obitosPts = {{ type: 'FeatureCollection', features: [] }};
let sinistrosPts = {{ type: 'FeatureCollection', features: [] }};
let pontosTipos = {{ type: 'FeatureCollection', features: [] }};
let heatSinistros = {{ points: [] }};
let heatObitos = {{ points: [] }};
let segRowsAll = [];
let segRowsByYear = [];
let segRowsByType = [];
let segRowsByYearType = [];
let geoAnalyticsLoaded = false;
let geoAnalyticsLoading = null;
let geoOverlaysLoaded = false;
let geoOverlaysLoading = null;

async function loadGeoData() {{
  const response = await fetch(GEO_DATA_URL, {{ cache: 'force-cache' }});
  if (!response.ok) throw new Error(`Falha ao carregar dados do mapa: ${{response.status}}`);
  const data = await response.json();
  roadRowsAll = data.roadRowsAll || [];
  roadRowsByYear = data.roadRowsByYear || [];
  roadRowsByYearType = data.roadRowsByYearType || [];
  malha = data.malha || {{ type: 'FeatureCollection', features: [] }};
  segRowsAll = (malha.features || []).map(f => ({{ ...f.properties }}));
}}

async function ensureGeoAnalyticsLoaded() {{
  if (geoAnalyticsLoaded) return;
  if (geoAnalyticsLoading) return geoAnalyticsLoading;
  geoAnalyticsLoading = fetch(GEO_ANALYTICS_URL, {{ cache: 'force-cache' }})
    .then((response) => {{
      if (!response.ok) throw new Error(`Falha ao carregar séries analíticas: ${{response.status}}`);
      return response.json();
    }})
    .then((data) => {{
      annualRows = data.annualRows || [];
      monthlyRows = data.monthlyRows || [];
      segRowsByYear = data.segRowsByYear || [];
      segRowsByType = data.segRowsByType || [];
      segRowsByYearType = data.segRowsByYearType || [];
      geoAnalyticsLoaded = true;
    }})
    .finally(() => {{ geoAnalyticsLoading = null; }});
  return geoAnalyticsLoading;
}}

async function ensureGeoOverlaysLoaded() {{
  if (geoOverlaysLoaded) return;
  if (geoOverlaysLoading) return geoOverlaysLoading;
  geoOverlaysLoading = fetch(GEO_OVERLAY_URL, {{ cache: 'force-cache' }})
    .then((response) => {{
      if (!response.ok) throw new Error(`Falha ao carregar camadas geográficas: ${{response.status}}`);
      return response.json();
    }})
    .then((data) => {{
      obitosPts = data.obitosPts || {{ type: 'FeatureCollection', features: [] }};
      sinistrosPts = data.sinistrosPts || {{ type: 'FeatureCollection', features: [] }};
      pontosTipos = data.pontosTipos || {{ type: 'FeatureCollection', features: [] }};
      heatSinistros = data.heatSinistros || {{ points: [] }};
      heatObitos = data.heatObitos || {{ points: [] }};
      geoOverlaysLoaded = true;
    }})
    .finally(() => {{ geoOverlaysLoading = null; }});
  return geoOverlaysLoading;
}}

function warmGeoAnalytics() {{
  const run = () => ensureGeoAnalyticsLoaded().then(() => renderAll()).catch(console.error);
  if ('requestIdleCallback' in window) window.requestIdleCallback(run, {{ timeout: 1200 }});
  else setTimeout(run, 250);
}}
function warmGeoOverlays() {{
  const run = () => ensureGeoOverlaysLoaded().then(() => renderAll()).catch(console.error);
  if ('requestIdleCallback' in window) window.requestIdleCallback(run, {{ timeout: 2000 }});
  else setTimeout(run, 700);
}}
const state = {{
  road: '', eventType: '', metric: '', order: '', topN: 8, year: '',
  showObitosGroup: false, showObitosPoints: false, showObitosMicros: false, obitosUseYear: false,
  showSinistrosGroup: false, showSinistrosPoints: false, showSinistrosMicros: false, sinistrosUseYear: false,
  showHeatGroup: false, showHeatObitos: false, showHeatSinistros: false, heatUseYear: false,
  showMalhaGroup: false, showMalhaSP: false, showMalhaSPA: false, showMalhaSPI: false, showMalhaSPM: false, showMalhaOUTRAS: false
}};
const metricNames = {{
  sinistros: 'Sinistros',
  obitos: 'Óbitos',
  sinistros_por_km: 'Sinistros/km',
  indice_letalidade: 'Letalidade (%)'
}};
const eventTypeNames = {{
  ALL: 'Todos os eventos',
  COLISAO: 'Colisão',
  CHOQUE: 'Choque',
  ATROPELAMENTO: 'Atropelamento',
  OUTROS: 'Outros'
}};

const fltRoad = document.getElementById('fltRoad');
const fltEventType = document.getElementById('fltEventType');
const fltMetric = document.getElementById('fltMetric');
const fltOrder = document.getElementById('fltOrder');
const fltYear = document.getElementById('fltYear');
const fltTopN = document.getElementById('fltTopN');
const topNLabel = document.getElementById('topNLabel');
const kpiBox = document.getElementById('geo-kpis');
const mapCaption = document.getElementById('map-caption');

function fmt(n, casas=0) {{
  return new Intl.NumberFormat('pt-BR', {{ minimumFractionDigits: casas, maximumFractionDigits: casas }}).format(Number(n || 0));
}}

function sortRows(rows, key) {{
  return [...rows].sort((a, b) => state.order === 'desc' ? (Number(b[key]) || 0) - (Number(a[key]) || 0) : (Number(a[key]) || 0) - (Number(b[key]) || 0));
}}

function pickColor(value, maxValue) {{
  const ratio = maxValue > 0 ? value / maxValue : 0;
  if (ratio >= 0.8) return '#7f1d1d';
  if (ratio >= 0.6) return '#b91c1c';
  if (ratio >= 0.4) return '#dc2626';
  if (ratio >= 0.2) return '#f97316';
  return '#facc15';
}}

function severityClass(value, maxValue) {{
  const ratio = maxValue > 0 ? value / maxValue : 0;
  if (ratio >= 0.8) return {{ label: 'Crítico', color: '#7f1d1d' }};
  if (ratio >= 0.6) return {{ label: 'Alto', color: '#b91c1c' }};
  if (ratio >= 0.35) return {{ label: 'Moderado', color: '#f97316' }};
  return {{ label: 'Baixo', color: '#facc15' }};
}}

function typeStyle(kind, family='sinistros') {{
  const k = String(kind || '').toUpperCase();
  if (family === 'obitos') {{
    if (k.includes('ATROPEL')) return {{ symbol: '▲', color: '#7c3aed', label: 'Atropelamento' }};
    if (k.includes('CHOQUE')) return {{ symbol: '◆', color: '#ea580c', label: 'Choque' }};
    if (k.includes('COLISAO')) return {{ symbol: '●', color: '#b91c1c', label: 'Colisão' }};
    return {{ symbol: '■', color: '#7f1d1d', label: 'Outros' }};
  }}
  if (k.includes('ATROPEL')) return {{ symbol: '▲', color: '#6d28d9', label: 'Atropelamento' }};
  if (k.includes('CHOQUE')) return {{ symbol: '◆', color: '#0891b2', label: 'Choque' }};
  if (k.includes('COLISAO')) return {{ symbol: '●', color: '#0e4d92', label: 'Colisão' }};
  return {{ symbol: '■', color: '#475569', label: 'Outros' }};
}}

function sameType(row, eventType=state.eventType) {{
  if (eventType === 'ALL') return true;
  const kind = String(row.evento_tipo || row.tp_sinistro_primario || '').toUpperCase();
  if (eventType === 'ATROPELAMENTO') return kind.includes('ATROPEL');
  if (eventType === 'CHOQUE') return kind.includes('CHOQUE');
  if (eventType === 'COLISAO') return kind.includes('COLISAO');
  return !kind.includes('ATROPEL') && !kind.includes('CHOQUE') && !kind.includes('COLISAO');
}}

function metricValue(row, metric=state.metric) {{
  const value = Number((row || {{}})[metric] || 0);
  return Number.isFinite(value) ? value : 0;
}}

function currentRoadBaseRows() {{
  let base = roadRowsAll;
  if (state.eventType !== 'ALL') {{
    base = roadRowsByYearType.filter(r => sameType(r) && (state.year === 'ALL' || String(r.ano_sinistro) === String(state.year)));
  }} else if (state.year !== 'ALL') {{
    base = roadRowsByYear.filter(r => String(r.ano_sinistro) === String(state.year));
  }}
  return base;
}}

function currentRoadRows() {{
  return currentRoadBaseRows().filter(r => state.road === 'ALL' || r.Rodovia === state.road);
}}

function currentSegRows() {{
  let base = segRowsAll;
  if (state.eventType !== 'ALL' && state.year !== 'ALL') {{
    base = segRowsByYearType.filter(r => sameType(r) && String(r.ano_sinistro) === String(state.year));
  }} else if (state.eventType !== 'ALL') {{
    base = segRowsByType.filter(r => sameType(r));
  }} else if (state.year !== 'ALL') {{
    base = segRowsByYear.filter(r => String(r.ano_sinistro) === String(state.year));
  }}
  return base.filter(r => state.road === 'ALL' || r.Rodovia === state.road);
}}

function timeSeriesRowsScoped() {{
  let base = state.eventType === 'ALL'
    ? roadRowsByYear
    : roadRowsByYearType.filter(r => sameType(r));
  base = base.filter(r => state.road === 'ALL' || r.Rodovia === state.road);
  const byYear = {{}};
  base.forEach(r => {{
    const y = String(r.ano_sinistro || '');
    if (!y) return;
    if (!byYear[y]) byYear[y] = {{ ano_sinistro: y, sinistros: 0, obitos: 0 }};
    byYear[y].sinistros += Number(r.sinistros || 0);
    byYear[y].obitos += Number(r.obitos || r.vitimas_fatais || 0);
  }});
  let out = Object.values(byYear).sort((a, b) => Number(a.ano_sinistro) - Number(b.ano_sinistro));
  if (state.year !== 'ALL') out = out.filter(r => String(r.ano_sinistro) === String(state.year));
  return out;
}}

function rebuildOptions(select, options, currentValue, allLabel=null) {{
  const placeholder = {{ value: '', label: 'Selecione um valor...', disabled: true }};
  const allItem = allLabel ? [{{ value: 'ALL', label: allLabel }}] : [];
  const items = [placeholder, ...allItem, ...options];
  select.innerHTML = items.map(opt => `<option value="${{opt.value}}"${{opt.disabled ? ' disabled' : ''}}>${{opt.label}}</option>`).join('');
  const allowed = items.filter(opt => !opt.disabled).map(opt => opt.value);
  const nextValue = allowed.includes(currentValue) ? currentValue : (allItem[0]?.value || options[0]?.value || '');
  select.value = nextValue;
  return nextValue;
}}

function availableEventTypes() {{
  const ordered = ['COLISAO', 'CHOQUE', 'ATROPELAMENTO', 'OUTROS'];
  return ordered.filter(evt => roadRowsByYearType.some(r => sameType(r, evt) && metricValue(r, state.metric) > 0));
}}

function availableYears() {{
  let base = state.eventType === 'ALL'
    ? roadRowsByYear
    : roadRowsByYearType.filter(r => sameType(r));
  base = base.filter(r => metricValue(r, state.metric) > 0);
  return [...new Set(base.map(r => String(r.ano_sinistro)).filter(Boolean))].sort((a, b) => Number(a) - Number(b));
}}

function availableRoadRows() {{
  return currentRoadBaseRows().filter(r => metricValue(r, state.metric) > 0);
}}

function fillRoadOptions() {{
  state.metric = rebuildOptions(fltMetric, [
    {{ value: 'sinistros', label: 'Sinistros' }},
    {{ value: 'obitos', label: 'Óbitos' }},
    {{ value: 'sinistros_por_km', label: 'Sinistros por km' }},
    {{ value: 'indice_letalidade', label: 'Letalidade (%)' }}
  ], state.metric);

  const eventOptions = availableEventTypes().map(evt => ({{ value: evt, label: eventTypeNames[evt] }}));
  state.eventType = rebuildOptions(fltEventType, eventOptions, state.eventType, 'Todos');

  const yearOptions = availableYears().map(y => ({{ value: y, label: y }}));
  state.year = rebuildOptions(fltYear, yearOptions, state.year, 'Todos os períodos ({anos_range})');

  const byRoad = {{}};
  availableRoadRows().forEach(r => {{
    const key = r.Rodovia;
    if (!key) return;
    if (!byRoad[key]) byRoad[key] = {{ value: key, total: 0 }};
    byRoad[key].total += metricValue(r, state.metric);
  }});
  const roadOptions = Object.values(byRoad)
    .sort((a, b) => Number(b.total || 0) - Number(a.total || 0) || a.value.localeCompare(b.value))
    .map(item => ({{
      value: item.value,
      label: `${{item.value}} · ${{fmt(item.total, state.metric.includes('km') || state.metric.includes('indice') ? 2 : 0)}} ${{metricNames[state.metric].toLowerCase()}}`
    }}));
  state.road = rebuildOptions(fltRoad, roadOptions, state.road, 'Todas as rodovias do mapa');
}}

function kpiCard(icon, title, value, note='', cls='') {{
  return `<div class="kpi ${{cls}}"><div class="i"><i class="${{icon}}"></i></div><div class="t">${{title}}</div><div class="v">${{value}}</div>${{note ? `<div class="l">${{note}}</div>` : ''}}</div>`;
}}

function updateKpis(rows, segs) {{
  const totalSin = rows.reduce((acc, r) => acc + Number(r.sinistros || 0), 0);
  const totalObi = rows.reduce((acc, r) => acc + Number(r.obitos || 0), 0);
  const mediaLet = rows.length ? rows.reduce((acc, r) => acc + Number(r.indice_letalidade || 0), 0) / rows.length : 0;
  const periodoTxt = state.year === 'ALL' ? '{anos_range}' : state.year;
  const tipoTxt = eventTypeNames[state.eventType] || 'Todos os eventos';
  const roadTxt = state.road === 'ALL' ? 'Malha completa' : state.road;
  kpiBox.innerHTML = [
    kpiCard('fa-regular fa-calendar', 'Período', periodoTxt, state.year === 'ALL' ? 'Visão acumulada' : 'Ano filtrado', 'ok'),
    kpiCard('fa-solid fa-filter', 'Tipo de evento', tipoTxt, 'Recorte analítico', 'ok'),
    kpiCard('fa-solid fa-road', 'Rodovia foco', roadTxt, state.road === 'ALL' ? 'Sem seleção fixa' : 'Seleção ativa'),
    kpiCard('fa-solid fa-network-wired', 'Rodovias no recorte', fmt(rows.length), 'Base do ranking'),
    kpiCard('fa-solid fa-route', 'Subtrechos no recorte', fmt(segs.length), 'Malha filtrada'),
    kpiCard('fa-solid fa-car-burst', 'Sinistros', fmt(totalSin), 'Eventos analisados'),
    kpiCard('fa-solid fa-crosshairs', 'Óbitos', fmt(totalObi), 'Eventos fatais', 'alert'),
    kpiCard('fa-solid fa-gauge-high', 'Letalidade média', `${{fmt(mediaLet, 2)}}%`, 'Índice médio', 'warn')
  ].join('');
  mapCaption.textContent = state.road === 'ALL'
    ? `Painel integrado da malha completa do DER/SP. Indicador: ${{metricNames[state.metric]}}. Tema: ${{tipoTxt}}. Período: ${{periodoTxt}}.`
    : `Painel integrado da rodovia ${{state.road}}. Indicador: ${{metricNames[state.metric]}}. Tema: ${{tipoTxt}}. Período: ${{periodoTxt}}.`;
}}

const mapa = L.map('map', {{ zoomControl: true }}).setView([-22.5, -48.5], 7);
const baseLight = L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{ attribution: '© OpenStreetMap © CARTO', maxZoom: 19 }}).addTo(mapa);
mapa.attributionControl.setPrefix(false);
window.addEventListener('load', () => setTimeout(() => mapa.invalidateSize(), 120));
window.addEventListener('resize', () => mapa.invalidateSize());
['paneMalha','paneHeat','paneSinPts','paneSinMicro','paneObPts','paneObMicro'].forEach(name => mapa.createPane(name));
mapa.getPane('paneMalha').style.zIndex = 320;
mapa.getPane('paneHeat').style.zIndex = 420;
mapa.getPane('paneSinPts').style.zIndex = 520;
mapa.getPane('paneSinMicro').style.zIndex = 530;
mapa.getPane('paneObPts').style.zIndex = 620;
mapa.getPane('paneObMicro').style.zIndex = 630;

let roadLayer = null;
const overlayGroups = {{
  malhaSP: L.layerGroup().addTo(mapa),
  malhaSPA: L.layerGroup().addTo(mapa),
  malhaSPI: L.layerGroup().addTo(mapa),
  malhaSPM: L.layerGroup().addTo(mapa),
  malhaOUTRAS: L.layerGroup().addTo(mapa),
  heatSinistros: L.layerGroup().addTo(mapa),
  heatObitos: L.layerGroup().addTo(mapa),
  sinistrosPoints: L.layerGroup().addTo(mapa),
  sinistrosMicros: L.layerGroup().addTo(mapa),
  obitosPoints: L.layerGroup().addTo(mapa),
  obitosMicros: L.layerGroup().addTo(mapa)
}};
const legendHtmlMap = {{
  obitosPoints: '<b>Legenda — Óbitos por categoria</b><br><span style="color:#b91c1c;font-weight:800">●</span> Colisão<br><span style="color:#ea580c;font-weight:800">◆</span> Choque<br><span style="color:#7c3aed;font-weight:800">▲</span> Atropelamento<br><span style="color:#7f1d1d;font-weight:800">■</span> Outros',
  obitosMicros: '<b>Legenda — Óbitos por categoria</b><br><span style="color:#b91c1c;font-weight:800">●</span> Colisão<br><span style="color:#ea580c;font-weight:800">◆</span> Choque<br><span style="color:#7c3aed;font-weight:800">▲</span> Atropelamento<br><span style="color:#7f1d1d;font-weight:800">■</span> Outros',
  sinistrosPoints: '<b>Legenda — Sinistros por categoria</b><br><span style="color:#0e4d92;font-weight:800">●</span> Colisão<br><span style="color:#0891b2;font-weight:800">◆</span> Choque<br><span style="color:#6d28d9;font-weight:800">▲</span> Atropelamento<br><span style="color:#475569;font-weight:800">■</span> Outros',
  sinistrosMicros: '<b>Legenda — Sinistros por categoria</b><br><span style="color:#0e4d92;font-weight:800">●</span> Colisão<br><span style="color:#0891b2;font-weight:800">◆</span> Choque<br><span style="color:#6d28d9;font-weight:800">▲</span> Atropelamento<br><span style="color:#475569;font-weight:800">■</span> Outros',
  heatObitos: '<b>Legenda — Mapa de calor de óbitos</b><br><span class="sw" style="background:#fee2e2"></span> Baixo<br><span class="sw" style="background:#ef4444"></span> Médio<br><span class="sw" style="background:#7f1d1d"></span> Alto',
  heatSinistros: '<b>Legenda — Mapa de calor de sinistros</b><br><span class="sw" style="background:#dbeafe"></span> Baixo<br><span class="sw" style="background:#2563eb"></span> Médio<br><span class="sw" style="background:#0b3a70"></span> Alto',
  malhaSP: '<b>Legenda — Malha estadual (SP/SPA/SPI/SPM)</b><br><span class="sw" style="background:#7f1d1d"></span> Crítico<br><span class="sw" style="background:#b91c1c"></span> Alto<br><span class="sw" style="background:#f97316"></span> Moderado<br><span class="sw" style="background:#facc15"></span> Baixo',
  malhaSPA: '<b>Legenda — Malha estadual (SP/SPA/SPI/SPM)</b><br><span class="sw" style="background:#7f1d1d"></span> Crítico<br><span class="sw" style="background:#b91c1c"></span> Alto<br><span class="sw" style="background:#f97316"></span> Moderado<br><span class="sw" style="background:#facc15"></span> Baixo',
  malhaSPI: '<b>Legenda — Malha estadual (SP/SPA/SPI/SPM/BR)</b><br><span class="sw" style="background:#7f1d1d"></span> Crítico<br><span class="sw" style="background:#b91c1c"></span> Alto<br><span class="sw" style="background:#f97316"></span> Moderado<br><span class="sw" style="background:#facc15"></span> Baixo',
  malhaSPM: '<b>Legenda — Malha estadual (SP/SPA/SPI/SPM/BR)</b><br><span class="sw" style="background:#7f1d1d"></span> Crítico<br><span class="sw" style="background:#b91c1c"></span> Alto<br><span class="sw" style="background:#f97316"></span> Moderado<br><span class="sw" style="background:#facc15"></span> Baixo',
  malhaOUTRAS: '<b>Legenda — Malha estadual (SP/SPA/SPI/SPM/BR)</b><br><span class="sw" style="background:#7f1d1d"></span> Crítico<br><span class="sw" style="background:#b91c1c"></span> Alto<br><span class="sw" style="background:#f97316"></span> Moderado<br><span class="sw" style="background:#facc15"></span> Baixo'
}};
const legendPriority = ['obitosMicros','obitosPoints','sinistrosMicros','sinistrosPoints','heatObitos','heatSinistros','malhaOUTRAS','malhaSPM','malhaSPI','malhaSPA','malhaSP'];
const legend = L.control({{ position: 'bottomright' }});
legend.onAdd = () => {{
  const d = L.DomUtil.create('div', 'legend-map');
  d.innerHTML = '<b>Legenda dinâmica</b><br>Ative uma camada na barra lateral.';
  legend._div = d;
  return d;
}};
legend.addTo(mapa);

const layerPanel = L.control({{ position: 'topleft' }});
layerPanel.onAdd = () => {{
  const div = L.DomUtil.create('div', 'layer-sidebar');
  div.innerHTML = `
    <h4>Camadas do mapa</h4>
    <div class="layer-group">
      <label class="master"><input id="grpObitos" type="checkbox" /> Óbitos</label>
      <div class="layer-items">
        <label><input id="lyObitosPoints" type="checkbox" /> Pontos</label>
        <label><input id="lyObitosMicros" type="checkbox" /> Micropontos</label>
        <label><input id="lyObitosYear" type="checkbox" /> Mostrar por ano do painel</label>
      </div>
    </div>
    <div class="layer-group">
      <label class="master"><input id="grpSinistros" type="checkbox" /> Sinistros</label>
      <div class="layer-items">
        <label><input id="lySinistrosPoints" type="checkbox" /> Pontos</label>
        <label><input id="lySinistrosMicros" type="checkbox" /> Micropontos</label>
        <label><input id="lySinistrosYear" type="checkbox" /> Mostrar por ano do painel</label>
      </div>
    </div>
    <div class="layer-group">
      <label class="master"><input id="grpHeat" type="checkbox" /> Mapas de calor</label>
      <div class="layer-items">
        <label><input id="lyHeatObitos" type="checkbox" /> Óbitos</label>
        <label><input id="lyHeatSinistros" type="checkbox" /> Sinistros</label>
        <label><input id="lyHeatYear" type="checkbox" /> Mostrar por ano do painel</label>
      </div>
    </div>
    <div class="layer-group">
      <label class="master"><input id="grpMalha" type="checkbox" /> Malha rodoviária estadual</label>
      <div class="layer-items">
        <label><input id="lyMalhaSP" type="checkbox" /> SP</label>
        <label><input id="lyMalhaSPA" type="checkbox" /> SPA</label>
        <label><input id="lyMalhaSPI" type="checkbox" /> SPI</label>
        <label><input id="lyMalhaSPM" type="checkbox" /> SPM</label>
        <label><input id="lyMalhaOUTRAS" type="checkbox" /> BR / outras</label>
      </div>
    </div>`;
  L.DomEvent.disableClickPropagation(div);
  return div;
}};
layerPanel.addTo(mapa);

function setLayerVisible(group, visible) {{
  if (visible) {{ if (!mapa.hasLayer(group)) group.addTo(mapa); }}
  else if (mapa.hasLayer(group)) group.remove();
}}
function pointMarker(latlng, kind, family='sinistros', micro=false) {{
  const style = typeStyle(kind, family);
  return L.marker(latlng, {{
    pane: micro ? (family === 'obitos' ? 'paneObMicro' : 'paneSinMicro') : (family === 'obitos' ? 'paneObPts' : 'paneSinPts'),
    icon: L.divIcon({{
      className: `sym-marker ${{micro ? 'micro' : 'point'}}`,
      html: `<span style="color:${{style.color}}">${{style.symbol}}</span>`,
      iconSize: micro ? [12, 12] : [16, 16],
      iconAnchor: micro ? [6, 6] : [8, 8]
    }})
  }});
}}
function pointPopup(ft, title, family='sinistros') {{
  const style = typeStyle(ft.properties.evento_tipo || ft.properties.tp_sinistro_primario, family);
  return `<b>${{title}}</b><br>` +
    `Ano: ${{ft.properties.ano_sinistro || '-'}}<br>` +
    `Rodovia: ${{ft.properties.Rodovia || '-'}}<br>` +
    `Município: ${{ft.properties.municipio || '-'}}<br>` +
    `Categoria: <span style="color:${{style.color}};font-weight:700">${{style.label}}</span>`;
}}
function roadCategoryFromName(roadName) {{
  const normalized = String(roadName || '').toUpperCase().trim();
  const feature = (malha.features || []).find(f => String(f?.properties?.Rodovia || '').toUpperCase().trim() === normalized);
  const raw = String(feature?.properties?.categoria_der || '').toUpperCase().trim();
  if (['SP', 'SPA', 'SPI', 'SPM'].includes(raw)) return raw;
  if (normalized.startsWith('BR ')) return 'OUTRAS';
  return raw || 'OUTRAS';
}}
function roadCategoryMatch(feature, cat) {{
  return roadCategoryFromName(feature?.properties?.Rodovia) === cat;
}}
function syncRoadLayerPanelFromFilter() {{
  const selectedRoad = fltRoad.value || state.road || '';
  const hasRoadSelection = !!selectedRoad;
  const showAllRoads = selectedRoad === 'ALL';
  const selectedCat = (!showAllRoads && hasRoadSelection) ? roadCategoryFromName(selectedRoad) : null;

  state.showMalhaGroup = hasRoadSelection;
  state.showMalhaSP = showAllRoads || selectedCat === 'SP';
  state.showMalhaSPA = showAllRoads || selectedCat === 'SPA';
  state.showMalhaSPI = showAllRoads || selectedCat === 'SPI';
  state.showMalhaSPM = showAllRoads || selectedCat === 'SPM';
  state.showMalhaOUTRAS = showAllRoads || selectedCat === 'OUTRAS';

  const master = document.getElementById('grpMalha');
  const flagMap = {{
    lyMalhaSP: state.showMalhaSP,
    lyMalhaSPA: state.showMalhaSPA,
    lyMalhaSPI: state.showMalhaSPI,
    lyMalhaSPM: state.showMalhaSPM,
    lyMalhaOUTRAS: state.showMalhaOUTRAS
  }};
  if (master) {{
    master.checked = hasRoadSelection;
    master.indeterminate = false;
  }}
  Object.entries(flagMap).forEach(([id, checked]) => {{
    const el = document.getElementById(id);
    if (el) el.checked = checked;
  }});
}}
function bindLayerPanel() {{
  const groups = [
    {{ master: 'grpObitos', groupKey: 'showObitosGroup', children: [['lyObitosPoints', 'showObitosPoints'], ['lyObitosMicros', 'showObitosMicros'], ['lyObitosYear', 'obitosUseYear']] }},
    {{ master: 'grpSinistros', groupKey: 'showSinistrosGroup', children: [['lySinistrosPoints', 'showSinistrosPoints'], ['lySinistrosMicros', 'showSinistrosMicros'], ['lySinistrosYear', 'sinistrosUseYear']] }},
    {{ master: 'grpHeat', groupKey: 'showHeatGroup', children: [['lyHeatObitos', 'showHeatObitos'], ['lyHeatSinistros', 'showHeatSinistros'], ['lyHeatYear', 'heatUseYear']] }},
    {{ master: 'grpMalha', groupKey: 'showMalhaGroup', children: [['lyMalhaSP', 'showMalhaSP'], ['lyMalhaSPA', 'showMalhaSPA'], ['lyMalhaSPI', 'showMalhaSPI'], ['lyMalhaSPM', 'showMalhaSPM'], ['lyMalhaOUTRAS', 'showMalhaOUTRAS']] }}
  ];
  groups.forEach(cfg => {{
    const master = document.getElementById(cfg.master);
    const children = cfg.children.map(([id, key]) => ({{ el: document.getElementById(id), key }})).filter(item => item.el);
    children.forEach(item => {{ item.el.checked = !!state[item.key]; }});
    const syncMaster = () => {{
      const checkedCount = children.filter(item => item.el.checked).length;
      master.checked = checkedCount === children.length && checkedCount > 0;
      master.indeterminate = checkedCount > 0 && checkedCount < children.length;
      state[cfg.groupKey] = checkedCount > 0;
    }};
    master.addEventListener('change', () => {{
      children.forEach(item => {{
        item.el.checked = master.checked;
        state[item.key] = master.checked;
      }});
      master.indeterminate = false;
      state[cfg.groupKey] = master.checked;
      renderAll();
    }});
    children.forEach(item => item.el.addEventListener('change', () => {{
      state[item.key] = item.el.checked;
      syncMaster();
      renderAll();
    }}));
    syncMaster();
  }});
}}
bindLayerPanel();
function activeLegendId() {{
  const visible = [];
  if (state.showMalhaGroup && state.showMalhaSP) visible.push('malhaSP');
  if (state.showMalhaGroup && state.showMalhaSPA) visible.push('malhaSPA');
  if (state.showMalhaGroup && state.showMalhaSPI) visible.push('malhaSPI');
  if (state.showMalhaGroup && state.showMalhaSPM) visible.push('malhaSPM');
  if (state.showMalhaGroup && state.showMalhaOUTRAS) visible.push('malhaOUTRAS');
  if (state.showHeatGroup && state.showHeatSinistros) visible.push('heatSinistros');
  if (state.showHeatGroup && state.showHeatObitos) visible.push('heatObitos');
  if (state.showSinistrosGroup && state.showSinistrosPoints) visible.push('sinistrosPoints');
  if (state.showSinistrosGroup && state.showSinistrosMicros) visible.push('sinistrosMicros');
  if (state.showObitosGroup && state.showObitosPoints) visible.push('obitosPoints');
  if (state.showObitosGroup && state.showObitosMicros) visible.push('obitosMicros');
  return legendPriority.find(id => visible.includes(id));
}}
function updateLegend() {{
  const id = activeLegendId();
  legend._div.innerHTML = legendHtmlMap[id] || '<b>Legenda dinâmica</b><br>Ative uma camada na barra lateral.';
}}

function drawMap(rows, segs) {{
  const maxMetric = Math.max(...segs.map(r => Number(r[state.metric] || 0)), 1);
  const segLookup = Object.fromEntries(segs.map(r => [r.trecho_id || r.Subtrecho, r]));
  const selectedYear = state.year === 'ALL' ? null : Number(state.year);
  const emptyRow = {{ sinistros: 0, obitos: 0, graves: 0, sinistros_por_km: 0, obitos_por_km: 0, indice_letalidade: 0 }};
  const featureCollection = {{
    type: 'FeatureCollection',
    features: malha.features.filter(f => state.road === 'ALL' || f.properties.Rodovia === state.road)
  }};
  Object.values(overlayGroups).forEach(g => g.clearLayers());

  const visibleBounds = L.featureGroup();
  const addMalhaCategoria = (cat, group, enabled) => {{
    setLayerVisible(group, state.showMalhaGroup && enabled);
    if (!(state.showMalhaGroup && enabled)) return;
    const lyr = L.geoJSON({{
      type: 'FeatureCollection',
      features: featureCollection.features.filter(f => roadCategoryMatch(f, cat))
    }}, {{
      pane: 'paneMalha',
      style: f => {{
        const key = f.properties.trecho_id || f.properties.Subtrecho;
        const row = segLookup[key] || ((state.year === 'ALL' && state.eventType === 'ALL') ? f.properties : emptyRow);
        const value = Number(row[state.metric] || 0);
        const sev = severityClass(value, maxMetric);
        return {{ color: sev.color, weight: Math.max(2, Math.min(9, 2 + (value / maxMetric) * 7)), opacity: 0.95 }};
      }},
      onEachFeature: (f, l) => {{
        const key = f.properties.trecho_id || f.properties.Subtrecho;
        const row = segLookup[key] || emptyRow;
        const value = Number(row[state.metric] || 0);
        const sev = severityClass(value, maxMetric);
        l.bindPopup(`<b>${{f.properties.Rodovia}}</b><br>Categoria DER: ${{f.properties.categoria_der}}<br>Subtrecho: ${{f.properties.Subtrecho}}<br>Classificação: <b>${{sev.label}}</b><br>Valor: ${{state.metric.includes('km') || state.metric.includes('indice') ? fmt(value, 2) : fmt(value)}}`);
        l.on('click', () => {{ state.road = f.properties.Rodovia; fltRoad.value = state.road; renderAll(); }});
      }}
    }}).addTo(group);
    visibleBounds.addLayer(lyr);
  }};
  addMalhaCategoria('SP', overlayGroups.malhaSP, state.showMalhaSP);
  addMalhaCategoria('SPA', overlayGroups.malhaSPA, state.showMalhaSPA);
  addMalhaCategoria('SPI', overlayGroups.malhaSPI, state.showMalhaSPI);
  addMalhaCategoria('SPM', overlayGroups.malhaSPM, state.showMalhaSPM);
  addMalhaCategoria('OUTRAS', overlayGroups.malhaOUTRAS, state.showMalhaOUTRAS);

  roadLayer = visibleBounds;
  if (visibleBounds.getBounds().isValid()) mapa.fitBounds(visibleBounds.getBounds(), {{ padding: [18, 18] }});
  else mapa.setView([-22.5, -48.5], 7);
  const bounds = visibleBounds.getBounds().isValid() ? visibleBounds.getBounds() : null;

  if (!geoOverlaysLoaded) {{
    if (!geoOverlaysLoading && (state.showObitosGroup || state.showSinistrosGroup || state.showHeatGroup)) {{
      ensureGeoOverlaysLoaded().then(() => renderAll()).catch(console.error);
    }}
    updateLegend();
    return;
  }}

  const filterPoint = (ft, useYear) => {{
    const coords = ft.geometry.coordinates;
    const sameYear = !(useYear && selectedYear) || Number(ft.properties.ano_sinistro) === selectedYear;
    const sameRoad = state.road === 'ALL' || ft.properties.Rodovia === state.road;
    const sameTypeEvent = state.eventType === 'ALL' || sameType(ft.properties);
    const sameArea = !bounds || state.road === 'ALL' || bounds.contains([coords[1], coords[0]]);
    return sameYear && sameRoad && sameTypeEvent && sameArea;
  }};

  setLayerVisible(overlayGroups.obitosPoints, state.showObitosGroup && state.showObitosPoints);
  if (state.showObitosGroup && state.showObitosPoints) {{
    obitosPts.features.filter(ft => filterPoint(ft, state.obitosUseYear)).forEach(ft => {{
      const coords = ft.geometry.coordinates;
      pointMarker([coords[1], coords[0]], ft.properties.evento_tipo || ft.properties.tp_sinistro_primario, 'obitos', false)
        .bindPopup(pointPopup(ft, 'Óbito', 'obitos'))
        .addTo(overlayGroups.obitosPoints);
    }});
  }}
  setLayerVisible(overlayGroups.obitosMicros, state.showObitosGroup && state.showObitosMicros);
  if (state.showObitosGroup && state.showObitosMicros) {{
    obitosPts.features.filter(ft => filterPoint(ft, state.obitosUseYear)).forEach(ft => {{
      const coords = ft.geometry.coordinates;
      pointMarker([coords[1], coords[0]], ft.properties.evento_tipo || ft.properties.tp_sinistro_primario, 'obitos', true)
        .bindPopup(pointPopup(ft, 'Óbito', 'obitos'))
        .addTo(overlayGroups.obitosMicros);
    }});
  }}
  setLayerVisible(overlayGroups.sinistrosPoints, state.showSinistrosGroup && state.showSinistrosPoints);
  if (state.showSinistrosGroup && state.showSinistrosPoints) {{
    sinistrosPts.features.filter(ft => filterPoint(ft, state.sinistrosUseYear)).forEach(ft => {{
      const coords = ft.geometry.coordinates;
      pointMarker([coords[1], coords[0]], ft.properties.evento_tipo || ft.properties.tp_sinistro_primario, 'sinistros', false)
        .bindPopup(pointPopup(ft, 'Sinistro', 'sinistros'))
        .addTo(overlayGroups.sinistrosPoints);
    }});
  }}
  setLayerVisible(overlayGroups.sinistrosMicros, state.showSinistrosGroup && state.showSinistrosMicros);
  if (state.showSinistrosGroup && state.showSinistrosMicros) {{
    sinistrosPts.features.filter(ft => filterPoint(ft, state.sinistrosUseYear)).forEach(ft => {{
      const coords = ft.geometry.coordinates;
      pointMarker([coords[1], coords[0]], ft.properties.evento_tipo || ft.properties.tp_sinistro_primario, 'sinistros', true)
        .bindPopup(pointPopup(ft, 'Sinistro', 'sinistros'))
        .addTo(overlayGroups.sinistrosMicros);
    }});
  }}
  setLayerVisible(overlayGroups.heatSinistros, state.showHeatGroup && state.showHeatSinistros);
  if (state.showHeatGroup && state.showHeatSinistros) {{
    const pts = heatSinistros.points.filter(p => {{
      const sameYear = !(state.heatUseYear && selectedYear) || Number(p[2]) === selectedYear;
      return !bounds || state.road === 'ALL' || bounds.contains([p[0], p[1]]);
    }});
    L.heatLayer(pts.map(p => [p[0], p[1], 0.4]), {{ pane: 'paneHeat', radius: 10, blur: 12, maxZoom: 10, gradient: {{ 0.2:'#dbeafe',0.5:'#2563eb',1:'#0b3a70' }} }}).addTo(overlayGroups.heatSinistros);
  }}
  setLayerVisible(overlayGroups.heatObitos, state.showHeatGroup && state.showHeatObitos);
  if (state.showHeatGroup && state.showHeatObitos) {{
    const pts = heatObitos.points.filter(p => {{
      const sameYear = !(state.heatUseYear && selectedYear) || Number(p[3]) === selectedYear;
      return !bounds || state.road === 'ALL' || bounds.contains([p[0], p[1]]);
    }});
    L.heatLayer(pts.map(p => [p[0], p[1], 0.3 + (p[2] || 0) * 2]), {{ pane: 'paneHeat', radius: 10, blur: 12, maxZoom: 10, gradient: {{ 0.2:'#fee2e2',0.5:'#ef4444',1:'#7f1d1d' }} }}).addTo(overlayGroups.heatObitos);
  }}
  updateLegend();
}}

function currentPeriodLabel() {{
  return state.year === 'ALL' ? '{anos_range}' : String(state.year);
}}

function metricAxisTitle(metric) {{
  if (metric === 'sinistros') return 'Sinistros (ocorrências)';
  if (metric === 'obitos') return 'Óbitos (vítimas)';
  if (metric === 'sinistros_por_km') return 'Sinistros por km (ocorrências/km)';
  return 'Letalidade (%)';
}}

function chartLayout(title, xTitle='', yTitle='') {{
  return {{
    title: {{ text: title, x: 0.02 }},
    paper_bgcolor: 'white',
    plot_bgcolor: 'white',
    font: {{ family: 'Inter, Segoe UI, sans-serif', size: 12, color: '#1f2937' }},
    margin: {{ l: 70, r: 20, t: 54, b: 54 }},
    height: 290,
    legend: {{ orientation: 'h', y: -0.2, x: 0.5, xanchor: 'center' }},
    xaxis: {{ title: xTitle, automargin: true }},
    yaxis: {{ title: yTitle, automargin: true }}
  }};
}}

function renderTimeSeries() {{
  const selectedYear = state.year === 'ALL' ? null : Number(state.year);
  const canUseMonthly = selectedYear && state.road === 'ALL' && state.eventType === 'ALL';

  if (canUseMonthly) {{
    const months = monthlyRows
      .filter(r => Number(r.ano_sinistro) === selectedYear)
      .sort((a, b) => Number(a.mes_sinistro) - Number(b.mes_sinistro));
    Plotly.react('timelineChart', [
      {{
        type: 'bar',
        name: 'Sinistros',
        x: months.map(r => String(r.mes_sinistro).padStart(2, '0')),
        y: months.map(r => Number(r.sinistros || 0)),
        marker: {{ color: '#0e4d92' }}
      }},
      {{
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Eventos fatais',
        x: months.map(r => String(r.mes_sinistro).padStart(2, '0')),
        y: months.map(r => Number(r.fatais || 0)),
        line: {{ color: '#d52b1e', width: 3 }}
      }}
    ], {{
      ...chartLayout(`Leitura mensal do ano ${{selectedYear}}`, 'Tempo (mês)', 'Quantidade (ocorrências / vítimas)'),
      height: 240,
      barmode: 'overlay',
      margin: {{ l: 50, r: 20, t: 54, b: 40 }}
    }}, {{ responsive: true, displaylogo: false }});
  }} else {{
    const scoped = timeSeriesRowsScoped();
    const years = scoped.map(r => Number(r.ano_sinistro));
    const sinistros = scoped.map(r => Number(r.sinistros || 0));
    const obitos = scoped.map(r => Number(r.obitos || 0));
    Plotly.react('timelineChart', [
      {{
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Sinistros',
        x: years,
        y: sinistros,
        line: {{ color: '#0e4d92', width: 3 }},
        marker: {{ size: 7, color: '#0e4d92' }}
      }},
      {{
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Óbitos',
        x: years,
        y: obitos,
        line: {{ color: '#d52b1e', width: 3, dash: 'dot' }},
        marker: {{ size: 7, color: '#d52b1e' }}
      }}
    ], {{
      ...chartLayout(`Evolução do recorte espacial · ${{currentPeriodLabel()}}`, 'Tempo (ano)', 'Quantidade (ocorrências / vítimas)'),
      height: 240,
      margin: {{ l: 50, r: 20, t: 54, b: 40 }},
      xaxis: {{ title: 'Tempo (ano)', tickmode: 'array', tickvals: years }},
      yaxis: {{ title: 'Quantidade (ocorrências / vítimas)' }}
    }}, {{ responsive: true, displaylogo: false }});
  }}

  const timeline = document.getElementById('timelineChart');
  timeline.removeAllListeners?.('plotly_click');
  timeline.on('plotly_click', ev => {{
    const year = String(ev.points[0].x).slice(0, 4);
    if (year && year !== 'NaN') {{
      state.year = year;
      fltYear.value = year;
      renderAll();
    }}
  }});
}}

function renderRoadRank(rows) {{
  const ranked = sortRows(rows, state.metric).slice(0, state.topN).reverse();
  const rankTitle = `Ranking de rodovias x ${{metricNames[state.metric]}}<br>em ${{currentPeriodLabel()}}`;
  Plotly.react('roadRankChart', [{{
    type: 'bar',
    orientation: 'h',
    x: ranked.map(r => r[state.metric]),
    y: ranked.map(r => r.Rodovia),
    text: ranked.map(r => state.metric.includes('km') || state.metric.includes('indice') ? fmt(r[state.metric], 2) : fmt(r[state.metric])),
    textposition: 'outside',
    cliponaxis: false,
    marker: {{ color: ranked.map(r => pickColor(Number(r[state.metric] || 0), Math.max(...ranked.map(x => Number(x[state.metric] || 0)), 1))) }}
  }}], {{
    ...chartLayout(rankTitle, metricAxisTitle(state.metric), 'Rodovia'),
    title: {{ text: rankTitle, x: 0.5, xanchor: 'center' }}
  }}, {{ responsive: true, displaylogo: false }});
  const rankChart = document.getElementById('roadRankChart');
  rankChart.removeAllListeners?.('plotly_click');
  rankChart.on('plotly_click', ev => {{
    state.road = ev.points[0].y;
    fltRoad.value = state.road;
    renderAll();
  }});
}}

function renderBubble(rows) {{
  const ranked = sortRows(rows, state.metric).slice(0, Math.min(6, rows.length));
  const total = ranked.reduce((acc, r) => acc + Number(r[state.metric] || 0), 0) || 1;
  Plotly.react('bubbleChart', [{{
    type: 'bar',
    x: ranked.map(r => r.Rodovia),
    y: ranked.map(r => (Number(r[state.metric] || 0) / total) * 100),
    customdata: ranked.map(r => r.Rodovia),
    text: ranked.map(r => `${{fmt((Number(r[state.metric] || 0) / total) * 100, 1)}}%`),
    textposition: 'outside',
    cliponaxis: false,
    marker: {{ color: ranked.map(r => pickColor(Number(r[state.metric] || 0), Math.max(...ranked.map(x => Number(x[state.metric] || 0)), 1))) }}
  }}], {{ ...chartLayout(`Participação no indicador · ${{currentPeriodLabel()}}`, 'Rodovia', 'Participação (%)'), margin: {{ l: 50, r: 20, t: 54, b: 70 }} }}, {{ responsive: true, displaylogo: false }});
  const bubble = document.getElementById('bubbleChart');
  bubble.removeAllListeners?.('plotly_click');
  bubble.on('plotly_click', ev => {{
    state.road = ev.points[0].customdata;
    fltRoad.value = state.road;
    renderAll();
  }});
}}

function renderSegments(segs) {{
  const ranked = sortRows(segs, state.metric).slice(0, state.topN).reverse();
  Plotly.react('segmentChart', [{{
    type: 'bar',
    orientation: 'h',
    x: ranked.map(r => r[state.metric]),
    y: ranked.map(r => `${{r.Subtrecho}} · km ${{fmt(r.KmInicial, 2)}}–${{fmt(r.KmFinal, 2)}}`),
    text: ranked.map(r => state.metric.includes('km') || state.metric.includes('indice') ? fmt(r[state.metric], 2) : fmt(r[state.metric])),
    textposition: 'outside',
    cliponaxis: false,
    marker: {{ color: '#0e4d92' }}
  }}], chartLayout(state.road === 'ALL' ? `Subtrechos em destaque no mapa · ${{currentPeriodLabel()}}` : `Subtrechos de ${{state.road}} · ${{currentPeriodLabel()}}`, metricAxisTitle(state.metric), 'Subtrecho / posição km'), {{ responsive: true, displaylogo: false }});
}}

function renderCompare(rows) {{
  let labels = [];
  let values = [];
  let colors = [];

  if (state.road !== 'ALL' && rows.length) {{
    const r = rows[0];
    const totalVisible = currentRoadRows().reduce((a, item) => a + Number(item[state.metric] || 0), 0);
    const current = Number(r[state.metric] || 0);
    const others = Math.max(0, totalVisible - current);
    labels = [state.road, 'Demais rodovias'];
    values = [current, others];
    colors = ['#0e4d92', '#cbd5e1'];
  }} else {{
    const ranked = sortRows(rows, state.metric).slice(0, Math.min(5, rows.length));
    const rankedSum = ranked.reduce((acc, r) => acc + Number(r[state.metric] || 0), 0);
    const totalAll = rows.reduce((acc, r) => acc + Number(r[state.metric] || 0), 0);
    const others = Math.max(0, totalAll - rankedSum);
    labels = ranked.map(r => r.Rodovia).concat(others > 0 ? ['Outras'] : []);
    values = ranked.map(r => Number(r[state.metric] || 0)).concat(others > 0 ? [others] : []);
    colors = ['#0e4d92', '#d52b1e', '#f7b500', '#0ea5e9', '#7c3aed', '#cbd5e1'];
  }}

  Plotly.react('compareChart', [{{
    type: 'pie',
    hole: 0.58,
    labels,
    values,
    textinfo: 'percent',
    textposition: 'inside',
    marker: {{ colors }},
    hovertemplate: '<b>%{{label}}</b><br>Valor: %{{value}}<br>Participação: %{{percent}}<extra></extra>'
  }}], {{
    ...chartLayout(`Composição do risco · ${{currentPeriodLabel()}}`),
    margin: {{ l: 10, r: 10, t: 54, b: 10 }},
    showlegend: true,
    legend: {{ orientation: 'h', y: -0.1, x: 0.5, xanchor: 'center' }}
  }}, {{ responsive: true, displaylogo: false }});
}}

function renderAll() {{
  state.metric = fltMetric.value || state.metric || 'sinistros';
  state.eventType = fltEventType.value || state.eventType || 'ALL';
  state.year = fltYear.value || state.year || 'ALL';
  state.road = fltRoad.value || state.road || 'ALL';
  state.order = fltOrder.value || 'desc';
  state.topN = Number(fltTopN.value);

  fillRoadOptions();
  fltMetric.value = state.metric;
  fltEventType.value = state.eventType;
  fltYear.value = state.year;
  fltRoad.value = state.road;

  syncRoadLayerPanelFromFilter();
  topNLabel.textContent = `Exibindo Top ${{state.topN}} · Filtros encadeados em Indicador → Tipo do evento → Período → Rodovias.`;

  const rows = currentRoadRows();
  const segs = currentSegRows();
  updateKpis(rows, segs);
  renderTimeSeries();
  drawMap(rows, segs);
  renderRoadRank(rows);
  renderBubble(rows);
  renderSegments(segs);
  renderCompare(rows);
}}

fltRoad.addEventListener('change', () => {{ state.road = fltRoad.value || 'ALL'; renderAll(); }});
fltEventType.addEventListener('change', renderAll);
fltMetric.addEventListener('change', renderAll);
fltOrder.addEventListener('change', renderAll);
fltYear.addEventListener('change', renderAll);
fltTopN.addEventListener('input', renderAll);
document.getElementById('btnReset').addEventListener('click', () => {{
  state.road = 'ALL';
  fltRoad.value = '';
  fltEventType.value = '';
  fltMetric.value = '';
  fltOrder.value = '';
  fltYear.value = '';
  fltTopN.value = '8';
  renderAll();
}});

(async function initGeoDashboard() {{
  try {{
    topNLabel.textContent = 'Carregando dados geográficos...';
    await loadGeoData();
    fillRoadOptions();
    fltRoad.value = state.road;
    fltEventType.value = state.eventType;
    fltMetric.value = state.metric;
    fltOrder.value = state.order;
    fltYear.value = state.year;
    renderAll();
    topNLabel.textContent = 'Mapa pronto. Todas as camadas iniciam desativadas e a malha é ligada ao selecionar uma rodovia.';
    warmGeoAnalytics();
  }} catch (err) {{
    console.error(err);
    topNLabel.textContent = 'Falha ao carregar os dados geográficos do painel.';
    mapCaption.textContent = 'Não foi possível carregar o painel analítico.';
  }}
}})();
</script>
"""

(DOCS / "analise_geografica.html").write_text(
    html_page("Dashboard 1 — Rodovias", geo_body, extra_head=geo_head),
    encoding="utf-8"
)

# ============ DASHBOARD 2 — SUBTRECHOS ============
focus_road_names = subtr.get("rodovias_foco", [])
focus_road_set = set(focus_road_names)
malha_focus_obj = {
    "type": "FeatureCollection",
    "features": [f_ for f_ in malha_obj["features"] if f_["properties"].get("Rodovia") in focus_road_set],
}
sub_asset_path = write_json_asset("geo/subtrechos_dashboard_main.json", {
    "focusMalha": malha_focus_obj,
    "topRoadsByType": subtr.get("top10_rodovias_por_tipo", {}),
    "focusRowsAll": subtr.get("subtrechos_foco", []),
    "focusRowsByType": subtr.get("subtrechos_foco_by_type", []),
})
sub_analytics_asset_path = write_json_asset("geo/subtrechos_dashboard_analytics.json", {
    "focusRowsByYearType": subtr.get("subtrechos_foco_by_year_type", []),
    "roadYearTypeRows": rod.get("all_by_year_type", []),
})
sub_overlay_asset_path = write_json_asset("geo/subtrechos_dashboard_overlays.json", {
    "obitosPts": json.load(open(OUT / "pontos_obitos.geojson", encoding="utf-8")),
    "sinistrosPts": json.load(open(OUT / "pontos_sinistros_amostra.geojson", encoding="utf-8")),
    "heatSinistros": json.load(open(OUT / "heat_points_sinistros.json", encoding="utf-8")),
    "heatObitos": json.load(open(OUT / "heat_points_obitos.json", encoding="utf-8")),
})

sub_body = f"""
<header class="hero">
  <h1>Dashboard 2 — Análise Detalhada por Subtrechos</h1>
  <p>Unidade espacial mínima: subtrecho DER/SP · foco nas top 10 rodovias de cada tipo de evento</p>
</header>
<main class="geo-main">
<section class="stats-shell">
  <h2>Estatística</h2>
  <p class="section-intro">Resumo consolidado do recorte por subtrecho, sincronizado aos filtros analíticos.</p>
  <div id="sub-kpis" class="kpis"></div>
</section>

<section class="filter-shell">
  <h2>Filtros analíticos</h2>
  <p class="section-intro">Este painel usa o subtrecho como menor unidade de análise e limita a leitura às rodovias líderes de cada tipo de evento.</p>
  <div class="filters">
    <label>Tipo de evento
      <select id="subEventType">
        <option value="" disabled selected>Selecione um valor...</option>
        <option value="ALL">Todos</option>
        <option value="COLISAO">Colisão</option>
        <option value="CHOQUE">Choque</option>
        <option value="ATROPELAMENTO">Atropelamento</option>
        <option value="OUTROS">Outros / não informado</option>
      </select>
    </label>
    <label>Rodovia do recorte
      <select id="subRoad">
        <option value="" disabled selected>Selecione um valor...</option>
      </select>
    </label>
    <label>Ano em destaque
      <select id="subYear">
        <option value="" disabled selected>Selecione um valor...</option>
        <option value="ALL">Todos os períodos ({anos_range})</option>
        {year_options_html}
      </select>
    </label>
    <label>Indicador
      <select id="subMetric">
        <option value="" disabled selected>Selecione um valor...</option>
        <option value="sinistros">Sinistros</option>
        <option value="obitos">Óbitos</option>
        <option value="sinistros_por_km">Sinistros por km</option>
        <option value="indice_letalidade">Letalidade (%)</option>
      </select>
    </label>
    <label>Visualização do mapa
      <select id="subViewMode">
        <option value="" disabled selected>Selecione um valor...</option>
        <option value="malha">Apenas malha viária</option>
        <option value="sinistrosPoints">Pontos de sinistros</option>
        <option value="sinistrosMicros">Micropontos de sinistros</option>
        <option value="obitosPoints">Pontos de óbitos</option>
        <option value="obitosMicros">Micropontos de óbitos</option>
        <option value="heatSinistros">Calor de sinistros</option>
        <option value="heatObitos">Calor de óbitos</option>
      </select>
    </label>
    <button id="subReset" type="button">Limpar seleção</button>
  </div>
  <div class="checkline">
    <span class="small-note">Os filtros definem o recorte analítico e a visualização; mapa e gráficos apenas se destacam mutuamente. O painel de camadas permanece sincronizado e não permite combinações sem sentido.</span>
  </div>
</section>

<section class="analytics-shell">
  <h2>Painel analítico</h2>
  <p id="sub-caption" class="section-intro">A rodovia selecionada fica sempre visível no mapa e nos cinco gráficos do painel, segmentada por subtrechos classificados segundo o evento e o período.</p>
  <div class="geo-board geo-board-inline">
    <section class="geo-panel map-panel">
      <div class="map-composite">
        <div class="map-stage">
          <h2><i class="fa-solid fa-route"></i> Rodovia segmentada por subtrechos</h2>
          <div id="mapSub"></div>
          <div class="layer-hint">
            <span class="layer-chip">Rodovia selecionada em foco</span>
            <span class="layer-chip">Subtrechos classificados</span>
            <span class="layer-chip">Evento e período sincronizados</span>
          </div>
        </div>

        <div class="geo-rail geo-rail-five">
          <section class="geo-panel">
            <h2><i class="fa-solid fa-chart-column"></i> Panorama macro do fenômeno</h2>
            <div id="subRoadChart" class="plot-host"></div>
          </section>

          <section class="geo-panel">
            <h2><i class="fa-solid fa-signal"></i> Subtrechos por classe</h2>
            <div id="subClassChart" class="plot-host"></div>
          </section>

          <section class="geo-panel">
            <h2><i class="fa-solid fa-road-circle-exclamation"></i> Subtrechos críticos</h2>
            <div id="subSegmentChart" class="plot-host"></div>
          </section>

          <section class="geo-panel">
            <h2><i class="fa-solid fa-chart-pie"></i> Composição dos líderes</h2>
            <div id="subShareChart" class="plot-host"></div>
          </section>

          <section class="geo-panel span-2">
            <h2><i class="fa-solid fa-clock"></i> Evolução temporal</h2>
            <div id="subSeriesChart" class="plot-host plot-timeline"></div>
          </section>
        </div>
      </div>
    </section>
  </div>
</section>
</main>
<script>
const SUB_DATA_URL = '{sub_asset_path}';
const SUB_ANALYTICS_URL = '{sub_analytics_asset_path}';
const SUB_OVERLAY_URL = '{sub_overlay_asset_path}';
let focusMalha = {{ type: 'FeatureCollection', features: [] }};
let topRoadsByType = {{}};
let focusRowsAll = [];
let focusRowsByType = [];
let focusRowsByYearType = [];
let roadYearTypeRows = [];
let obitosPts2 = {{ type: 'FeatureCollection', features: [] }};
let sinistrosPts2 = {{ type: 'FeatureCollection', features: [] }};
let heatSinistros2 = {{ points: [] }};
let heatObitos2 = {{ points: [] }};
let subAnalyticsLoaded = false;
let subAnalyticsLoading = null;
let subOverlaysLoaded = false;
let subOverlaysLoading = null;

async function loadSubData() {{
  const response = await fetch(SUB_DATA_URL, {{ cache: 'force-cache' }});
  if (!response.ok) throw new Error(`Falha ao carregar dados dos subtrechos: ${{response.status}}`);
  const data = await response.json();
  focusMalha = data.focusMalha || {{ type: 'FeatureCollection', features: [] }};
  topRoadsByType = data.topRoadsByType || {{}};
  focusRowsAll = data.focusRowsAll || [];
  focusRowsByType = data.focusRowsByType || [];
}}

async function ensureSubAnalyticsLoaded() {{
  if (subAnalyticsLoaded) return;
  if (subAnalyticsLoading) return subAnalyticsLoading;
  subAnalyticsLoading = fetch(SUB_ANALYTICS_URL, {{ cache: 'force-cache' }})
    .then((response) => {{
      if (!response.ok) throw new Error(`Falha ao carregar séries dos subtrechos: ${{response.status}}`);
      return response.json();
    }})
    .then((data) => {{
      focusRowsByYearType = data.focusRowsByYearType || [];
      roadYearTypeRows = data.roadYearTypeRows || [];
      subAnalyticsLoaded = true;
    }})
    .finally(() => {{ subAnalyticsLoading = null; }});
  return subAnalyticsLoading;
}}

async function ensureSubOverlaysLoaded() {{
  if (subOverlaysLoaded) return;
  if (subOverlaysLoading) return subOverlaysLoading;
  subOverlaysLoading = fetch(SUB_OVERLAY_URL, {{ cache: 'force-cache' }})
    .then((response) => {{
      if (!response.ok) throw new Error(`Falha ao carregar camadas dos subtrechos: ${{response.status}}`);
      return response.json();
    }})
    .then((data) => {{
      obitosPts2 = data.obitosPts || {{ type: 'FeatureCollection', features: [] }};
      sinistrosPts2 = data.sinistrosPts || {{ type: 'FeatureCollection', features: [] }};
      heatSinistros2 = data.heatSinistros || {{ points: [] }};
      heatObitos2 = data.heatObitos || {{ points: [] }};
      subOverlaysLoaded = true;
    }})
    .finally(() => {{ subOverlaysLoading = null; }});
  return subOverlaysLoading;
}}

function warmSubAnalytics() {{
  const run = () => ensureSubAnalyticsLoaded().then(() => renderSubDash()).catch(console.error);
  if ('requestIdleCallback' in window) window.requestIdleCallback(run, {{ timeout: 1200 }});
  else setTimeout(run, 250);
}}
function warmSubOverlays() {{
  const run = () => ensureSubOverlaysLoaded().then(() => renderSubDash()).catch(console.error);
  if ('requestIdleCallback' in window) window.requestIdleCallback(run, {{ timeout: 2000 }});
  else setTimeout(run, 700);
}}
const eventTypeNames2 = {{ ALL: 'Todos', COLISAO: 'Colisão', CHOQUE: 'Choque', ATROPELAMENTO: 'Atropelamento', OUTROS: 'Outros' }};
const metricNames2 = {{ sinistros: 'Sinistros', obitos: 'Óbitos', sinistros_por_km: 'Sinistros/km', indice_letalidade: 'Letalidade (%)' }};
const viewModeNames2 = {{
  malha: 'Apenas malha viária',
  sinistrosPoints: 'Pontos de sinistros',
  sinistrosMicros: 'Micropontos de sinistros',
  obitosPoints: 'Pontos de óbitos',
  obitosMicros: 'Micropontos de óbitos',
  heatSinistros: 'Calor de sinistros',
  heatObitos: 'Calor de óbitos'
}};
const viewModeMetric2 = {{
  malha: null,
  sinistrosPoints: 'sinistros',
  sinistrosMicros: 'sinistros',
  heatSinistros: 'sinistros',
  obitosPoints: 'obitos',
  obitosMicros: 'obitos',
  heatObitos: 'obitos'
}};
const state2 = {{
  eventType: 'ALL', road: 'ALL', metric: 'sinistros', year: 'ALL', viewMode: 'malha',
  highlightRoad: null, highlightSegment: null,
  showObitosGroup: false, showObitosPoints: false, showObitosMicros: false, obitosUseYear: true,
  showSinistrosGroup: false, showSinistrosPoints: false, showSinistrosMicros: false, sinistrosUseYear: true,
  showHeatGroup: false, showHeatObitos: false, showHeatSinistros: false, heatUseYear: true,
  showMalhaGroup: true, showMalhaSP: true, showMalhaSPA: true, showMalhaSPI: true, showMalhaSPM: true, showMalhaOUTRAS: true
}};

const subEventType = document.getElementById('subEventType');
const subRoad = document.getElementById('subRoad');
const subMetric = document.getElementById('subMetric');
const subViewMode = document.getElementById('subViewMode');
const subYear = document.getElementById('subYear');
const subKpis = document.getElementById('sub-kpis');
const subCaption = document.getElementById('sub-caption');

function syncViewState2(origin='render') {{
  const ratioMetric = ['sinistros_por_km', 'indice_letalidade'].includes(state2.metric);
  if (origin === 'metric') {{
    if (state2.metric === 'obitos') {{
      if (state2.viewMode === 'sinistrosPoints') state2.viewMode = 'obitosPoints';
      if (state2.viewMode === 'sinistrosMicros') state2.viewMode = 'obitosMicros';
      if (state2.viewMode === 'heatSinistros') state2.viewMode = 'heatObitos';
    }} else if (state2.metric === 'sinistros') {{
      if (state2.viewMode === 'obitosPoints') state2.viewMode = 'sinistrosPoints';
      if (state2.viewMode === 'obitosMicros') state2.viewMode = 'sinistrosMicros';
      if (state2.viewMode === 'heatObitos') state2.viewMode = 'heatSinistros';
    }}
  }}
  if (ratioMetric) state2.viewMode = 'malha';
  if (!viewModeNames2[state2.viewMode]) state2.viewMode = 'malha';
  const flags = {{
    showObitosGroup: false, showObitosPoints: false, showObitosMicros: false,
    showSinistrosGroup: false, showSinistrosPoints: false, showSinistrosMicros: false,
    showHeatGroup: false, showHeatObitos: false, showHeatSinistros: false
  }};
  if (!ratioMetric) {{
    if (state2.viewMode === 'obitosPoints') {{ flags.showObitosGroup = true; flags.showObitosPoints = true; }}
    if (state2.viewMode === 'obitosMicros') {{ flags.showObitosGroup = true; flags.showObitosMicros = true; }}
    if (state2.viewMode === 'sinistrosPoints') {{ flags.showSinistrosGroup = true; flags.showSinistrosPoints = true; }}
    if (state2.viewMode === 'sinistrosMicros') {{ flags.showSinistrosGroup = true; flags.showSinistrosMicros = true; }}
    if (state2.viewMode === 'heatSinistros') {{ flags.showHeatGroup = true; flags.showHeatSinistros = true; }}
    if (state2.viewMode === 'heatObitos') {{ flags.showHeatGroup = true; flags.showHeatObitos = true; }}
  }}
  Object.assign(state2, flags);
  if ((origin === 'filter' || origin === 'layer') && viewModeMetric2[state2.viewMode]) {{
    state2.metric = viewModeMetric2[state2.viewMode];
    subMetric.value = state2.metric;
  }}
  [...subViewMode.options].forEach(opt => {{
    opt.disabled = ratioMetric && opt.value !== 'malha';
  }});
  subViewMode.value = state2.viewMode;
  [...document.querySelectorAll('input[name="subViewLayer2"]')].forEach(el => {{
    el.checked = el.value === state2.viewMode;
    el.disabled = ratioMetric && el.value !== 'malha';
  }});
}}

function fmt2(n, casas=0) {{
  return new Intl.NumberFormat('pt-BR', {{ minimumFractionDigits: casas, maximumFractionDigits: casas }}).format(Number(n || 0));
}}
function pickColor2(value, maxValue) {{
  const ratio = maxValue > 0 ? value / maxValue : 0;
  if (ratio >= 0.8) return '#7f1d1d';
  if (ratio >= 0.6) return '#b91c1c';
  if (ratio >= 0.35) return '#f97316';
  return '#facc15';
}}
function typeStyle2(kind, family='sinistros') {{
  const k = String(kind || '').toUpperCase();
  if (family === 'obitos') {{
    if (k.includes('ATROPEL')) return {{ symbol: '▲', color: '#7c3aed', label: 'Atropelamento' }};
    if (k.includes('CHOQUE')) return {{ symbol: '◆', color: '#ea580c', label: 'Choque' }};
    if (k.includes('COLISAO')) return {{ symbol: '●', color: '#b91c1c', label: 'Colisão' }};
    return {{ symbol: '■', color: '#7f1d1d', label: 'Outros' }};
  }}
  if (k.includes('ATROPEL')) return {{ symbol: '▲', color: '#6d28d9', label: 'Atropelamento' }};
  if (k.includes('CHOQUE')) return {{ symbol: '◆', color: '#0891b2', label: 'Choque' }};
  if (k.includes('COLISAO')) return {{ symbol: '●', color: '#0e4d92', label: 'Colisão' }};
  return {{ symbol: '■', color: '#475569', label: 'Outros' }};
}}
function sameType2(row, eventType=state2.eventType) {{
  if (eventType === 'ALL') return true;
  return String(row.evento_tipo || row.tp_sinistro_primario || '').toUpperCase() === eventType;
}}
function focusRoadNames2() {{
  return [...new Set((focusMalha.features || []).map(f => f.properties.Rodovia))];
}}
function metricValue2(row, metric=state2.metric) {{
  const value = Number((row || {{}})[metric] || 0);
  return Number.isFinite(value) ? value : 0;
}}
function isPositiveMetric2(row, metric=state2.metric) {{
  return metricValue2(row, metric) > 0;
}}
function aggregateRoadRows2(rows) {{
  const byRoad = {{}};
  rows.forEach(r => {{
    const key = r.Rodovia;
    if (!key) return;
    if (!byRoad[key]) byRoad[key] = {{ Rodovia: key, sinistros: 0, obitos: 0, sinistros_por_km: 0, indice_letalidade: 0, n: 0 }};
    byRoad[key].sinistros += Number(r.sinistros || 0);
    byRoad[key].obitos += Number(r.obitos || 0);
    byRoad[key].sinistros_por_km += Number(r.sinistros_por_km || 0);
    byRoad[key].indice_letalidade += Number(r.indice_letalidade || 0);
    byRoad[key].n += 1;
  }});
  return Object.values(byRoad).map(r => ({{
    ...r,
    sinistros_por_km: r.n ? r.sinistros_por_km / r.n : 0,
    indice_letalidade: r.n ? r.indice_letalidade / r.n : 0,
  }}));
}}
function availableEventTypes2() {{
  return ['COLISAO', 'CHOQUE', 'ATROPELAMENTO', 'OUTROS'].filter(evt => focusRowsByType.some(r => sameType2(r, evt)));
}}
function roadPool2(eventType=state2.eventType) {{
  const preset = (topRoadsByType[eventType] || []).map(r => r.Rodovia).filter(Boolean);
  if (preset.length) return preset;
  const focusRoads = focusRoadNames2();
  const rows = aggregateRoadRows2(roadYearTypeRows.filter(r => sameType2(r, eventType) && focusRoads.includes(r.Rodovia)))
    .sort((a, b) => Number(b.sinistros || 0) - Number(a.sinistros || 0))
    .slice(0, 10);
  return rows.map(r => r.Rodovia);
}}
function availableYears2() {{
  const pool = roadPool2();
  let rows = roadYearTypeRows.filter(r => sameType2(r) && pool.includes(r.Rodovia));
  if (state2.road !== 'ALL') rows = rows.filter(r => r.Rodovia === state2.road);
  return [...new Set(rows.map(r => String(r.ano_sinistro)))].sort((a, b) => Number(a) - Number(b));
}}
function availableViewModes2() {{
  if (['sinistros_por_km', 'indice_letalidade'].includes(state2.metric)) return ['malha'];
  if (state2.metric === 'obitos') return ['malha', 'obitosPoints', 'obitosMicros', 'heatObitos'];
  return ['malha', 'sinistrosPoints', 'sinistrosMicros', 'heatSinistros'];
}}
function rebuildOptions2(select, options, currentValue, allLabel=null) {{
  const placeholder = {{ value: '', label: 'Selecione um valor...', disabled: true }};
  const allItem = allLabel ? [{{ value: 'ALL', label: allLabel }}] : [];
  const items = [placeholder, ...allItem, ...options];
  select.innerHTML = items.map(opt => `<option value="${{opt.value}}"${{opt.disabled ? ' disabled' : ''}}>${{opt.label}}</option>`).join('');
  const allowed = items.filter(opt => !opt.disabled).map(opt => opt.value);
  const nextValue = allowed.includes(currentValue) ? currentValue : (allItem[0]?.value || options[0]?.value || '');
  select.value = nextValue;
  return nextValue;
}}
function syncFilterOptions2() {{
  const validEvents = availableEventTypes2();
  const eventOptions = validEvents.map(evt => ({{ value: evt, label: eventTypeNames2[evt] }}));
  state2.eventType = rebuildOptions2(subEventType, eventOptions, state2.eventType, 'Todos');
  const roads = roadPool2().map(name => ({{ value: name, label: name }}));
  state2.road = rebuildOptions2(subRoad, roads, state2.road, 'Todas as rodovias do recorte');
  const years = availableYears2().map(y => ({{ value: y, label: y }}));
  state2.year = rebuildOptions2(subYear, years, state2.year, 'Todos os períodos ({anos_range})');
  state2.metric = rebuildOptions2(subMetric, [
    {{ value: 'sinistros', label: 'Sinistros' }},
    {{ value: 'obitos', label: 'Óbitos' }},
    {{ value: 'sinistros_por_km', label: 'Sinistros por km' }},
    {{ value: 'indice_letalidade', label: 'Letalidade (%)' }}
  ], state2.metric);
  const modes = availableViewModes2().map(mode => ({{ value: mode, label: viewModeNames2[mode] }}));
  state2.viewMode = rebuildOptions2(subViewMode, modes, state2.viewMode);
  syncViewState2('render');
}}
function currentRows2() {{
  const pool = roadPool2();
  let base = state2.year === 'ALL'
    ? focusRowsByType.filter(r => sameType2(r) && pool.includes(r.Rodovia))
    : focusRowsByYearType.filter(r => sameType2(r) && String(r.ano_sinistro) === String(state2.year) && pool.includes(r.Rodovia));
  if (state2.road !== 'ALL') base = base.filter(r => r.Rodovia === state2.road);
  return base;
}}
function roadRanking2() {{
  const pool = roadPool2();
  let rows = state2.year === 'ALL'
    ? aggregateRoadRows2(roadYearTypeRows.filter(r => sameType2(r) && pool.includes(r.Rodovia)))
    : roadYearTypeRows.filter(r => sameType2(r) && String(r.ano_sinistro) === String(state2.year) && pool.includes(r.Rodovia));
  if (state2.road !== 'ALL') rows = rows.filter(r => r.Rodovia === state2.road);
  return [...rows].sort((a, b) => Number(b[state2.metric] || 0) - Number(a[state2.metric] || 0));
}}
function seriesRows2() {{
  const pool = roadPool2();
  let rows = roadYearTypeRows.filter(r => sameType2(r) && pool.includes(r.Rodovia));
  if (state2.road !== 'ALL') rows = rows.filter(r => r.Rodovia === state2.road);
  const byYear = {{}};
  rows.forEach(r => {{
    const y = String(r.ano_sinistro);
    if (!byYear[y]) byYear[y] = {{ ano_sinistro: y, sinistros: 0, obitos: 0, sinistros_por_km: 0, indice_letalidade: 0, n: 0 }};
    byYear[y].sinistros += Number(r.sinistros || 0);
    byYear[y].obitos += Number(r.obitos || 0);
    byYear[y].sinistros_por_km += Number(r.sinistros_por_km || 0);
    byYear[y].indice_letalidade += Number(r.indice_letalidade || 0);
    byYear[y].n += 1;
  }});
  let out = Object.values(byYear).sort((a, b) => Number(a.ano_sinistro) - Number(b.ano_sinistro)).map(r => ({{
    ...r,
    sinistros_por_km: r.n ? r.sinistros_por_km / r.n : 0,
    indice_letalidade: r.n ? r.indice_letalidade / r.n : 0,
  }}));
  if (state2.year !== 'ALL') out = out.filter(r => String(r.ano_sinistro) === String(state2.year));
  return out;
}}
function kpiCard2(icon, title, value, note='', cls='') {{
  return `<div class="kpi ${{cls}}"><div class="i"><i class="${{icon}}"></i></div><div class="t">${{title}}</div><div class="v">${{value}}</div>${{note ? `<div class="l">${{note}}</div>` : ''}}</div>`;
}}
function updateKpis2(rows, roads) {{
  const totalSin = rows.reduce((a, r) => a + Number(r.sinistros || 0), 0);
  const totalObi = rows.reduce((a, r) => a + Number(r.obitos || 0), 0);
  const roadTxt = state2.road === 'ALL' ? 'Top 10 do tipo' : state2.road;
  const segRoadTxt = state2.road === 'ALL' ? 'Todas as rodovias do recorte' : state2.road;
  subKpis.innerHTML = [
    kpiCard2('fa-solid fa-route', 'Unidade mínima', 'Subtrecho', 'Recorte espacial', 'ok'),
    kpiCard2('fa-solid fa-filter', 'Tipo de evento', eventTypeNames2[state2.eventType], 'Filtro ativo', 'ok'),
    kpiCard2('fa-regular fa-calendar', 'Período', state2.year === 'ALL' ? '{anos_range}' : state2.year, 'Recorte temporal'),
    kpiCard2('fa-solid fa-layer-group', 'Visualização', viewModeNames2[state2.viewMode], 'Modo cartográfico sincronizado'),
    kpiCard2('fa-solid fa-road', 'Rodovia foco', roadTxt, state2.road === 'ALL' ? 'Sem seleção fixa' : 'Seleção ativa'),
    kpiCard2('fa-solid fa-network-wired', 'Rodovias líderes', fmt2(roads.length), 'Ranking do tipo'),
    kpiCard2('fa-solid fa-road-circle-exclamation', 'Subtrechos no recorte', fmt2(rows.length), 'Base analítica'),
    kpiCard2('fa-solid fa-car-burst', 'Sinistros', fmt2(totalSin), 'Eventos analisados'),
    kpiCard2('fa-solid fa-crosshairs', 'Óbitos', fmt2(totalObi), 'Eventos fatais', 'alert')
  ].join('');
  subCaption.textContent = `Filtros no comando: ${{eventTypeNames2[state2.eventType]}} · Indicador: ${{metricNames2[state2.metric]}} · Visualização: ${{viewModeNames2[state2.viewMode]}} · Ano: ${{state2.year === 'ALL' ? '{anos_range}' : state2.year}} · Recorte: ${{roadTxt}} · Subtrechos exibidos: ${{segRoadTxt}}.`;
}}
function metricAxisTitle2(metric) {{
  if (metric === 'sinistros') return 'Sinistros (ocorrências)';
  if (metric === 'obitos') return 'Óbitos (vítimas)';
  if (metric === 'sinistros_por_km') return 'Sinistros por km (ocorrências/km)';
  return 'Letalidade (%)';
}}
function layout2(title, xTitle='', yTitle='') {{
  return {{
    title: {{ text: title, x: 0.02 }},
    paper_bgcolor: 'white',
    plot_bgcolor: 'white',
    font: {{ family: 'Inter, Segoe UI, sans-serif', size: 12, color: '#1f2937' }},
    margin: {{ l: 70, r: 20, t: 54, b: 54 }},
    height: 290,
    legend: {{ orientation: 'h', y: -0.2, x: 0.5, xanchor: 'center' }},
    xaxis: {{ title: xTitle, automargin: true }},
    yaxis: {{ title: yTitle, automargin: true }}
  }};
}}
const mapSub = L.map('mapSub', {{ zoomControl: true }}).setView([-22.5, -48.5], 7);
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{ attribution: '© OpenStreetMap © CARTO', maxZoom: 19 }}).addTo(mapSub);
mapSub.attributionControl.setPrefix(false);
window.addEventListener('load', () => setTimeout(() => mapSub.invalidateSize(), 120));
window.addEventListener('resize', () => mapSub.invalidateSize());
['paneMalha2','paneHeat2','paneSinPts2','paneSinMicro2','paneObPts2','paneObMicro2'].forEach(name => mapSub.createPane(name));
mapSub.getPane('paneMalha2').style.zIndex = 320;
mapSub.getPane('paneHeat2').style.zIndex = 420;
mapSub.getPane('paneSinPts2').style.zIndex = 520;
mapSub.getPane('paneSinMicro2').style.zIndex = 530;
mapSub.getPane('paneObPts2').style.zIndex = 620;
mapSub.getPane('paneObMicro2').style.zIndex = 630;
let focusLayer = null;
const overlayGroups2 = {{
  malhaSP: L.layerGroup().addTo(mapSub),
  malhaSPA: L.layerGroup().addTo(mapSub),
  malhaSPI: L.layerGroup().addTo(mapSub),
  malhaSPM: L.layerGroup().addTo(mapSub),
  malhaOUTRAS: L.layerGroup().addTo(mapSub),
  heatSinistros: L.layerGroup().addTo(mapSub),
  heatObitos: L.layerGroup().addTo(mapSub),
  sinistrosPoints: L.layerGroup().addTo(mapSub),
  sinistrosMicros: L.layerGroup().addTo(mapSub),
  obitosPoints: L.layerGroup().addTo(mapSub),
  obitosMicros: L.layerGroup().addTo(mapSub)
}};
const legend2 = L.control({{ position: 'bottomright' }});
legend2.onAdd = () => {{
  const d = L.DomUtil.create('div', 'legend-map');
  legend2._div = d;
  d.innerHTML = '<b>Legenda dinâmica</b><br>Ative uma camada na barra lateral.';
  return d;
}};
legend2.addTo(mapSub);
const layerPanel2 = L.control({{ position: 'topleft' }});
layerPanel2.onAdd = () => {{
  const div = L.DomUtil.create('div', 'layer-sidebar');
  div.innerHTML = `
    <h4>Camadas do mapa</h4>
    <div class="layer-group">
      <label class="master"><input id="grpView2" type="checkbox" checked disabled /> Visualização sincronizada</label>
      <div class="layer-items">
        <label><input name="subViewLayer2" id="lyOnlyMalha2" type="radio" value="malha" checked /> Apenas malha viária</label>
        <label><input name="subViewLayer2" id="lySinistrosPoints2" type="radio" value="sinistrosPoints" /> Pontos de sinistros</label>
        <label><input name="subViewLayer2" id="lySinistrosMicros2" type="radio" value="sinistrosMicros" /> Micropontos de sinistros</label>
        <label><input name="subViewLayer2" id="lyObitosPoints2" type="radio" value="obitosPoints" /> Pontos de óbitos</label>
        <label><input name="subViewLayer2" id="lyObitosMicros2" type="radio" value="obitosMicros" /> Micropontos de óbitos</label>
        <label><input name="subViewLayer2" id="lyHeatSinistros2" type="radio" value="heatSinistros" /> Calor de sinistros</label>
        <label><input name="subViewLayer2" id="lyHeatObitos2" type="radio" value="heatObitos" /> Calor de óbitos</label>
      </div>
    </div>
    <div class="layer-group">
      <label class="master"><input id="grpRoads2" type="checkbox" checked /> Rodovias</label>
      <div id="roadLayerList2" class="layer-items"></div>
    </div>`;
  L.DomEvent.disableClickPropagation(div);
  return div;
}};
layerPanel2.addTo(mapSub);
function setLayerVisible2(group, visible) {{
  if (visible) {{ if (!mapSub.hasLayer(group)) group.addTo(mapSub); }}
  else if (mapSub.hasLayer(group)) group.remove();
}}
function pointMarker2(latlng, kind, family='sinistros', micro=false) {{
  const style = typeStyle2(kind, family);
  return L.marker(latlng, {{
    pane: micro ? (family === 'obitos' ? 'paneObMicro2' : 'paneSinMicro2') : (family === 'obitos' ? 'paneObPts2' : 'paneSinPts2'),
    icon: L.divIcon({{
      className: `sym-marker ${{micro ? 'micro' : 'point'}}`,
      html: `<span style="color:${{style.color}}">${{style.symbol}}</span>`,
      iconSize: micro ? [12, 12] : [16, 16],
      iconAnchor: micro ? [6, 6] : [8, 8]
    }})
  }});
}}
function pointPopup2(ft, title, family='sinistros') {{
  const style = typeStyle2(ft.properties.evento_tipo || ft.properties.tp_sinistro_primario, family);
  return `<b>${{title}}</b><br>` +
    `Ano: ${{ft.properties.ano_sinistro || '-'}}<br>` +
    `Rodovia: ${{ft.properties.Rodovia || '-'}}<br>` +
    `Município: ${{ft.properties.municipio || '-'}}<br>` +
    `Categoria: <span style="color:${{style.color}};font-weight:700">${{style.label}}</span>`;
}}
function roadCategoryFromName2(roadName) {{
  const normalized = String(roadName || '').toUpperCase().trim();
  const feature = (focusMalha.features || []).find(f => String(f?.properties?.Rodovia || '').toUpperCase().trim() === normalized);
  const raw = String(feature?.properties?.categoria_der || '').toUpperCase().trim();
  if (['SP', 'SPA', 'SPI', 'SPM'].includes(raw)) return raw;
  if (normalized.startsWith('BR ')) return 'OUTRAS';
  return raw || 'OUTRAS';
}}
function roadCategoryMatch2(feature, cat) {{
  return roadCategoryFromName2(feature?.properties?.Rodovia) === cat;
}}
function updateLegend2() {{
  const priority = [
    ['obitosMicros', state2.showObitosGroup && state2.showObitosMicros, '<b>Legenda — Óbitos por categoria</b><br><span style="color:#b91c1c;font-weight:800">●</span> Colisão<br><span style="color:#ea580c;font-weight:800">◆</span> Choque<br><span style="color:#7c3aed;font-weight:800">▲</span> Atropelamento<br><span style="color:#7f1d1d;font-weight:800">■</span> Outros'],
    ['obitosPoints', state2.showObitosGroup && state2.showObitosPoints, '<b>Legenda — Óbitos por categoria</b><br><span style="color:#b91c1c;font-weight:800">●</span> Colisão<br><span style="color:#ea580c;font-weight:800">◆</span> Choque<br><span style="color:#7c3aed;font-weight:800">▲</span> Atropelamento<br><span style="color:#7f1d1d;font-weight:800">■</span> Outros'],
    ['sinistrosMicros', state2.showSinistrosGroup && state2.showSinistrosMicros, '<b>Legenda — Sinistros por categoria</b><br><span style="color:#0e4d92;font-weight:800">●</span> Colisão<br><span style="color:#0891b2;font-weight:800">◆</span> Choque<br><span style="color:#6d28d9;font-weight:800">▲</span> Atropelamento<br><span style="color:#475569;font-weight:800">■</span> Outros'],
    ['sinistrosPoints', state2.showSinistrosGroup && state2.showSinistrosPoints, '<b>Legenda — Sinistros por categoria</b><br><span style="color:#0e4d92;font-weight:800">●</span> Colisão<br><span style="color:#0891b2;font-weight:800">◆</span> Choque<br><span style="color:#6d28d9;font-weight:800">▲</span> Atropelamento<br><span style="color:#475569;font-weight:800">■</span> Outros'],
    ['heatObitos', state2.showHeatGroup && state2.showHeatObitos, '<b>Legenda — Mapa de calor de óbitos</b><br><span class="sw" style="background:#fee2e2"></span> Baixo<br><span class="sw" style="background:#ef4444"></span> Médio<br><span class="sw" style="background:#7f1d1d"></span> Alto'],
    ['heatSinistros', state2.showHeatGroup && state2.showHeatSinistros, '<b>Legenda — Mapa de calor de sinistros</b><br><span class="sw" style="background:#dbeafe"></span> Baixo<br><span class="sw" style="background:#2563eb"></span> Médio<br><span class="sw" style="background:#0b3a70"></span> Alto'],
    ['malha', state2.showMalhaGroup, '<b>Legenda — Rodovias</b><br><span class="sw" style="background:#7f1d1d"></span> Crítico<br><span class="sw" style="background:#b91c1c"></span> Alto<br><span class="sw" style="background:#f97316"></span> Moderado<br><span class="sw" style="background:#facc15"></span> Baixo']
  ];
  const item = priority.find(x => x[1]);
  legend2._div.innerHTML = item ? item[2] : '<b>Legenda dinâmica</b><br>Ative uma camada na barra lateral.';
}}
function syncRoadLayerPanel2() {{
  const host = document.getElementById('roadLayerList2');
  const master = document.getElementById('grpRoads2');
  if (!host || !master) return;
  const roads = roadPool2();
  const allSelected = state2.road === 'ALL';
  host.innerHTML = roads.map(name => `<label><input class="road-layer-toggle2" type="checkbox" value="${{name}}" ${{(allSelected || state2.road === name) ? 'checked' : ''}} /> ${{name}}</label>`).join('');
  master.checked = !!state2.showMalhaGroup;
  master.indeterminate = false;

  [...host.querySelectorAll('.road-layer-toggle2')].forEach(el => el.addEventListener('change', () => {{
    if (!el.checked) {{
      state2.road = 'ALL';
      subRoad.value = 'ALL';
      state2.highlightRoad = null;
      state2.highlightSegment = null;
      syncRoadLayerPanel2();
      renderSubDash();
      return;
    }}
    state2.showMalhaGroup = true;
    state2.road = el.value;
    subRoad.value = state2.road;
    state2.highlightRoad = state2.road;
    state2.highlightSegment = null;
    syncRoadLayerPanel2();
    renderSubDash();
  }}));
}}

function bindLayerPanel2() {{
  const radios = [...document.querySelectorAll('input[name="subViewLayer2"]')];
  const syncRadios = () => {{
    const ratioMetric = ['sinistros_por_km', 'indice_letalidade'].includes(state2.metric);
    radios.forEach(el => {{
      el.checked = el.value === state2.viewMode;
      el.disabled = ratioMetric && el.value !== 'malha';
    }});
  }};
  radios.forEach(el => el.addEventListener('change', () => {{
    if (!el.checked) return;
    state2.viewMode = el.value;
    subViewMode.value = state2.viewMode;
    syncViewState2('layer');
    renderSubDash();
  }}));

  const master = document.getElementById('grpRoads2');
  master.addEventListener('change', () => {{
    state2.showMalhaGroup = master.checked;
    if (master.checked) {{
      state2.road = 'ALL';
      subRoad.value = 'ALL';
    }}
    syncRoadLayerPanel2();
    renderSubDash();
  }});

  syncRadios();
  syncRoadLayerPanel2();
}}
bindLayerPanel2();
function drawMap2(rows) {{
  const allowedRoads = roadPool2();
  const lookup = Object.fromEntries(rows.map(r => [r.trecho_id, r]));
  const maxMetric = Math.max(...rows.map(r => Number(r[state2.metric] || 0)), 1);
  const selectedYear = state2.year === 'ALL' ? null : Number(state2.year);
  const focusedRoad = state2.road !== 'ALL' ? state2.road : null;
  if (focusedRoad && state2.showMalhaGroup) {{
    const cat = roadCategoryFromName2(focusedRoad);
    if (cat === 'SP') state2.showMalhaSP = true;
    if (cat === 'SPA') state2.showMalhaSPA = true;
    if (cat === 'SPI') state2.showMalhaSPI = true;
    if (cat === 'SPM') state2.showMalhaSPM = true;
    if (cat === 'OUTRAS') state2.showMalhaOUTRAS = true;
  }}
  const fc = {{
    type: 'FeatureCollection',
    features: focusMalha.features.filter(f => allowedRoads.includes(f.properties.Rodovia) && (state2.road === 'ALL' || f.properties.Rodovia === state2.road))
  }};
  Object.values(overlayGroups2).forEach(g => g.clearLayers());
  const visibleBounds = L.featureGroup();
  const addCat = (cat, group, enabled) => {{
    setLayerVisible2(group, state2.showMalhaGroup && enabled);
    if (!(state2.showMalhaGroup && enabled)) return;
    const lyr = L.geoJSON({{ type: 'FeatureCollection', features: fc.features.filter(f => roadCategoryMatch2(f, cat)) }}, {{
      pane: 'paneMalha2',
      style: f => {{
        const row = lookup[f.properties.trecho_id] || {{}};
        const value = Number(row[state2.metric] || 0);
        const isSeg = state2.highlightSegment === f.properties.trecho_id;
        const isRoad = !isSeg && state2.highlightRoad === f.properties.Rodovia;
        return {{
          color: pickColor2(value, maxMetric),
          weight: isSeg ? 8 : isRoad ? 6 : value > 0 ? 5 : 2,
          opacity: isSeg || isRoad ? 1 : 0.92,
          dashArray: isSeg ? '8 4' : null
        }};
      }},
      onEachFeature: (f, l) => {{
        const row = lookup[f.properties.trecho_id] || {{ sinistros: 0, obitos: 0, sinistros_por_km: 0, indice_letalidade: 0 }};
        l.bindPopup(`<b>${{f.properties.Rodovia}}</b><br>Categoria DER: ${{f.properties.categoria_der}}<br>Subtrecho: ${{f.properties.Subtrecho}}<br>Tipo: ${{eventTypeNames2[state2.eventType]}}<br>Ano: ${{state2.year === 'ALL' ? '{anos_range}' : state2.year}}<br>Sinistros: ${{fmt2(row.sinistros)}}<br>Óbitos: ${{fmt2(row.obitos)}}`);
        l.on('click', () => {{
          state2.road = f.properties.Rodovia;
          subRoad.value = state2.road;
          state2.highlightRoad = f.properties.Rodovia;
          state2.highlightSegment = f.properties.trecho_id;
          renderSubDash();
        }});
      }}
    }}).addTo(group);
    visibleBounds.addLayer(lyr);
  }};
  addCat('SP', overlayGroups2.malhaSP, state2.showMalhaSP);
  addCat('SPA', overlayGroups2.malhaSPA, state2.showMalhaSPA);
  addCat('SPI', overlayGroups2.malhaSPI, state2.showMalhaSPI);
  addCat('SPM', overlayGroups2.malhaSPM, state2.showMalhaSPM);
  addCat('OUTRAS', overlayGroups2.malhaOUTRAS, state2.showMalhaOUTRAS);
  focusLayer = visibleBounds;
  if (visibleBounds.getBounds().isValid()) mapSub.fitBounds(visibleBounds.getBounds(), {{ padding: [18, 18] }});
  const bounds = visibleBounds.getBounds().isValid() ? visibleBounds.getBounds() : null;
  if (!subOverlaysLoaded) {{
    if (!subOverlaysLoading && (state2.showObitosGroup || state2.showSinistrosGroup || state2.showHeatGroup)) {{
      ensureSubOverlaysLoaded().then(() => renderSubDash()).catch(console.error);
    }}
    updateLegend2();
    return;
  }}
  const filterPoint2 = (ft, useYear) => {{
    const coords = ft.geometry.coordinates;
    const sameYear = !(useYear && selectedYear) || Number(ft.properties.ano_sinistro) === selectedYear;
    const sameRoad = allowedRoads.includes(ft.properties.Rodovia) && (state2.road === 'ALL' || ft.properties.Rodovia === state2.road);
    const sameTypeEvent = sameType2(ft.properties);
    const sameArea = !bounds || state2.road === 'ALL' || bounds.contains([coords[1], coords[0]]);
    return sameYear && sameRoad && sameTypeEvent && sameArea;
  }};
  setLayerVisible2(overlayGroups2.obitosPoints, state2.showObitosGroup && state2.showObitosPoints);
  if (state2.showObitosGroup && state2.showObitosPoints) {{
    obitosPts2.features.filter(ft => filterPoint2(ft, state2.obitosUseYear)).forEach(ft => {{
      const coords = ft.geometry.coordinates;
      pointMarker2([coords[1], coords[0]], ft.properties.evento_tipo || ft.properties.tp_sinistro_primario, 'obitos', false).bindPopup(pointPopup2(ft, 'Óbito', 'obitos')).addTo(overlayGroups2.obitosPoints);
    }});
  }}
  setLayerVisible2(overlayGroups2.obitosMicros, state2.showObitosGroup && state2.showObitosMicros);
  if (state2.showObitosGroup && state2.showObitosMicros) {{
    obitosPts2.features.filter(ft => filterPoint2(ft, state2.obitosUseYear)).forEach(ft => {{
      const coords = ft.geometry.coordinates;
      pointMarker2([coords[1], coords[0]], ft.properties.evento_tipo || ft.properties.tp_sinistro_primario, 'obitos', true).bindPopup(pointPopup2(ft, 'Óbito', 'obitos')).addTo(overlayGroups2.obitosMicros);
    }});
  }}
  setLayerVisible2(overlayGroups2.sinistrosPoints, state2.showSinistrosGroup && state2.showSinistrosPoints);
  if (state2.showSinistrosGroup && state2.showSinistrosPoints) {{
    sinistrosPts2.features.filter(ft => filterPoint2(ft, state2.sinistrosUseYear)).forEach(ft => {{
      const coords = ft.geometry.coordinates;
      pointMarker2([coords[1], coords[0]], ft.properties.evento_tipo || ft.properties.tp_sinistro_primario, 'sinistros', false).bindPopup(pointPopup2(ft, 'Sinistro', 'sinistros')).addTo(overlayGroups2.sinistrosPoints);
    }});
  }}
  setLayerVisible2(overlayGroups2.sinistrosMicros, state2.showSinistrosGroup && state2.showSinistrosMicros);
  if (state2.showSinistrosGroup && state2.showSinistrosMicros) {{
    sinistrosPts2.features.filter(ft => filterPoint2(ft, state2.sinistrosUseYear)).forEach(ft => {{
      const coords = ft.geometry.coordinates;
      pointMarker2([coords[1], coords[0]], ft.properties.evento_tipo || ft.properties.tp_sinistro_primario, 'sinistros', true).bindPopup(pointPopup2(ft, 'Sinistro', 'sinistros')).addTo(overlayGroups2.sinistrosMicros);
    }});
  }}
  setLayerVisible2(overlayGroups2.heatSinistros, state2.showHeatGroup && state2.showHeatSinistros);
  if (state2.showHeatGroup && state2.showHeatSinistros) {{
    const pts = heatSinistros2.points.filter(p => {{
      const sameYear = !(state2.heatUseYear && selectedYear) || Number(p[2]) === selectedYear;
      return !bounds || state2.road === 'ALL' || bounds.contains([p[0], p[1]]);
    }});
    L.heatLayer(pts.map(p => [p[0], p[1], 0.4]), {{ pane: 'paneHeat2', radius: 10, blur: 12, maxZoom: 10, gradient: {{ 0.2:'#dbeafe',0.5:'#2563eb',1:'#0b3a70' }} }}).addTo(overlayGroups2.heatSinistros);
  }}
  setLayerVisible2(overlayGroups2.heatObitos, state2.showHeatGroup && state2.showHeatObitos);
  if (state2.showHeatGroup && state2.showHeatObitos) {{
    const pts = heatObitos2.points.filter(p => {{
      const sameYear = !(state2.heatUseYear && selectedYear) || Number(p[3]) === selectedYear;
      return !bounds || state2.road === 'ALL' || bounds.contains([p[0], p[1]]);
    }});
    L.heatLayer(pts.map(p => [p[0], p[1], 0.3 + (p[2] || 0) * 2]), {{ pane: 'paneHeat2', radius: 10, blur: 12, maxZoom: 10, gradient: {{ 0.2:'#fee2e2',0.5:'#ef4444',1:'#7f1d1d' }} }}).addTo(overlayGroups2.heatObitos);
  }}
  updateLegend2();
}}
function severityBucket2(value, maxValue) {{
  const ratio = maxValue > 0 ? value / maxValue : 0;
  if (ratio >= 0.8) return 'Crítico';
  if (ratio >= 0.6) return 'Alto';
  if (ratio >= 0.35) return 'Moderado';
  return 'Baixo';
}}
function renderRoadChart2(rows) {{
  const scoped = state2.road === 'ALL' ? currentRows2() : currentRows2().filter(r => r.Rodovia === state2.road);
  const maxMetric = Math.max(...scoped.map(r => Number(r[state2.metric] || 0)), 1);
  const buckets = ['Baixo', 'Moderado', 'Alto', 'Crítico'];
  const totals = {{ 'Baixo': 0, 'Moderado': 0, 'Alto': 0, 'Crítico': 0 }};
  scoped.forEach(r => {{
    const bucket = severityBucket2(Number(r[state2.metric] || 0), maxMetric);
    totals[bucket] += Number(r[state2.metric] || 0);
  }});
  Plotly.react('subRoadChart', [{{
    type: 'bar',
    x: buckets,
    y: buckets.map(label => totals[label] || 0),
    text: buckets.map(label => ['sinistros_por_km', 'indice_letalidade'].includes(state2.metric) ? fmt2(totals[label] || 0, 2) : fmt2(totals[label] || 0)),
    textposition: 'outside',
    cliponaxis: false,
    marker: {{ color: ['#facc15', '#f97316', '#b91c1c', '#7f1d1d'] }}
  }}], {{ ...layout2(`Panorama macro · ${{eventTypeNames2[state2.eventType]}}`, 'Classe de criticidade', metricAxisTitle2(state2.metric)), margin: {{ l: 50, r: 20, t: 54, b: 50 }} }}, {{ responsive: true, displaylogo: false }});
}}
function renderClassChart2(rows) {{
  const scoped = state2.road === 'ALL' ? rows : rows.filter(r => r.Rodovia === state2.road);
  const maxMetric = Math.max(...scoped.map(r => Number(r[state2.metric] || 0)), 1);
  const counts = {{ 'Baixo': 0, 'Moderado': 0, 'Alto': 0, 'Crítico': 0 }};
  scoped.forEach(r => {{
    const bucket = severityBucket2(Number(r[state2.metric] || 0), maxMetric);
    counts[bucket] += 1;
  }});
  const labels = ['Baixo', 'Moderado', 'Alto', 'Crítico'];
  Plotly.react('subClassChart', [{{
    type: 'bar',
    x: labels,
    y: labels.map(label => counts[label] || 0),
    marker: {{ color: ['#facc15', '#f97316', '#b91c1c', '#7f1d1d'] }},
    text: labels.map(label => counts[label] || 0),
    textposition: 'outside',
    cliponaxis: false
  }}], {{ ...layout2('Subtrechos por classe', 'Classe de criticidade', 'Subtrechos (quantidade)'), margin: {{ l: 50, r: 20, t: 54, b: 50 }} }}, {{ responsive: true, displaylogo: false }});
}}
function renderSegChart2(rows, roads) {{
  const baseRoad = state2.road !== 'ALL' ? state2.road : null;
  const scoped = baseRoad ? rows.filter(r => r.Rodovia === baseRoad) : rows;
  const top = [...scoped].sort((a, b) => Number(b[state2.metric] || 0) - Number(a[state2.metric] || 0)).slice(0, 10).reverse();
  const maxMetric = Math.max(...top.map(r => Number(r[state2.metric] || 0)), 1);
  Plotly.react('subSegmentChart', [{{
    type: 'bar',
    orientation: 'h',
    x: top.map(r => Number(r[state2.metric] || 0)),
    y: top.map(r => `km ${{fmt2(r.KmInicial, 2)}}–${{fmt2(r.KmFinal, 2)}}`),
    text: top.map(r => ['sinistros_por_km', 'indice_letalidade'].includes(state2.metric) ? fmt2(r[state2.metric], 2) : fmt2(r[state2.metric])),
    textposition: 'outside',
    cliponaxis: false,
    customdata: top.map(r => [r.trecho_id, r.Rodovia]),
    marker: {{ color: top.map(r => pickColor2(Number(r[state2.metric] || 0), maxMetric)) }}
  }}], layout2(baseRoad ? `Subtrechos críticos · ${{baseRoad}}` : 'Subtrechos críticos', metricAxisTitle2(state2.metric), 'Subtrecho / posição km'), {{ responsive: true, displaylogo: false }});
  const el = document.getElementById('subSegmentChart');
  if (el.removeAllListeners) el.removeAllListeners('plotly_click');
  el.on('plotly_click', (evt) => {{
    const data = evt.points?.[0]?.customdata || [];
    if (!data.length) return;
    state2.road = data[1];
    subRoad.value = state2.road;
    state2.highlightSegment = data[0];
    state2.highlightRoad = data[1];
    renderSubDash();
  }});
}}
function renderSeries2(rows) {{
  Plotly.react('subSeriesChart', [{{
    type: 'scatter', mode: 'lines+markers',
    x: rows.map(r => r.ano_sinistro),
    y: rows.map(r => Number(r[state2.metric] || 0)),
    line: {{ color: '#0e4d92', width: 3 }},
    marker: {{ size: 7, color: '#0e4d92' }}
  }}], {{ ...layout2(`Evolução temporal · ${{metricNames2[state2.metric]}}`, 'Tempo (ano)', metricAxisTitle2(state2.metric)), height: 240, margin: {{ l: 50, r: 20, t: 54, b: 40 }} }}, {{ responsive: true, displaylogo: false }});
}}
function renderShare2(rows) {{
  const baseRoad = state2.road !== 'ALL' ? state2.road : null;
  const scoped = baseRoad ? rows.filter(r => r.Rodovia === baseRoad) : rows;
  const top = [...scoped].sort((a, b) => Number(b[state2.metric] || 0) - Number(a[state2.metric] || 0)).slice(0, 5);
  Plotly.react('subShareChart', [{{
    type: 'pie',
    hole: 0.58,
    labels: top.map(r => `${{r.Rodovia}} · km ${{fmt2(r.KmInicial, 1)}}`),
    values: top.map(r => Number(r[state2.metric] || 0)),
    customdata: top.map(r => [r.trecho_id, r.Rodovia]),
    textinfo: 'percent',
    textposition: 'inside',
    marker: {{ color: ['#0e4d92', '#d52b1e', '#f7b500', '#0ea5e9', '#7c3aed'] }},
    hovertemplate: '<b>%{{label}}</b><br>Valor: %{{value}}<br>Participação: %{{percent}}<extra></extra>'
  }}], {{ ...layout2('Composição dos líderes'), margin: {{ l: 10, r: 10, t: 54, b: 10 }}, showlegend: true, legend: {{ orientation: 'h', y: -0.1, x: 0.5, xanchor: 'center' }} }}, {{ responsive: true, displaylogo: false }});
  const el = document.getElementById('subShareChart');
  if (el.removeAllListeners) el.removeAllListeners('plotly_click');
  el.on('plotly_click', (evt) => {{
    const data = evt.points?.[0]?.customdata || [];
    if (!data.length) return;
    state2.road = data[1];
    subRoad.value = state2.road;
    state2.highlightSegment = data[0];
    state2.highlightRoad = data[1];
    renderSubDash();
  }});
}}
function renderSubDash() {{
  state2.metric = subMetric.value || state2.metric;
  state2.eventType = subEventType.value || state2.eventType;
  state2.road = subRoad.value || state2.road;
  state2.year = subYear.value || state2.year;
  state2.viewMode = subViewMode.value || state2.viewMode;
  syncFilterOptions2();
  syncRoadLayerPanel2();
  const rows = currentRows2();
  const roads = roadRanking2();
  const series = seriesRows2();
  const validSegments = new Set(rows.map(r => r.trecho_id));
  const validRoads = new Set([...rows.map(r => r.Rodovia), ...roads.map(r => r.Rodovia)]);
  if (state2.highlightSegment && !validSegments.has(state2.highlightSegment)) state2.highlightSegment = null;
  if (state2.highlightRoad && !validRoads.has(state2.highlightRoad)) state2.highlightRoad = null;
  updateKpis2(rows, roads);
  drawMap2(rows);
  renderRoadChart2(roads);
  renderClassChart2(rows);
  renderSegChart2(rows, roads);
  renderSeries2(series);
  renderShare2(rows);
}}
subEventType.addEventListener('change', () => {{ state2.highlightRoad = null; state2.highlightSegment = null; renderSubDash(); }});
subRoad.addEventListener('change', () => {{ state2.highlightRoad = null; state2.highlightSegment = null; renderSubDash(); }});
subMetric.addEventListener('change', () => {{ state2.highlightRoad = null; state2.highlightSegment = null; renderSubDash(); }});
subViewMode.addEventListener('change', () => {{ renderSubDash(); }});
subYear.addEventListener('change', () => {{ state2.highlightRoad = null; state2.highlightSegment = null; renderSubDash(); }});
document.getElementById('subReset').addEventListener('click', () => {{
  subEventType.value = 'ALL';
  subMetric.value = 'sinistros';
  subViewMode.value = 'malha';
  subYear.value = 'ALL';
  state2.road = 'ALL';
  state2.viewMode = 'malha';
  state2.highlightRoad = null;
  state2.highlightSegment = null;
  syncViewState2('filter');
  renderSubDash();
}});
(async function initSubDashboard() {{
  try {{
    subCaption.textContent = 'Carregando dados dos subtrechos...';
    await loadSubData();
    syncFilterOptions2();
    syncViewState2('filter');
    renderSubDash();
    subCaption.textContent = 'Painel pronto. Filtros, camadas e gráficos agora seguem a mesma hierarquia analítica.';
    warmSubAnalytics();
  }} catch (err) {{
    console.error(err);
    subCaption.textContent = 'Não foi possível carregar o painel de subtrechos.';
  }}
}})();
</script>
"""

(DOCS / "analise_subtrechos.html").write_text(
    html_page("Dashboard 2 — Subtrechos", sub_body, extra_head=geo_head),
    encoding="utf-8"
)

# ============ GUIA DE ACESSO ============
guia_body = f"""
<header class="hero">
  <h1>Guia de Acesso</h1>
  <p>Navegação do painel Infosiga SP</p>
</header>
<main>
<section><h2>Páginas</h2>
<ul>
  <li><a href="index.html"><i class="fa-solid fa-house"></i> Portal</a> — visão geral, KPIs e acesso aos recursos</li>
  <li><a href="dashboard_principal.html"><i class="fa-solid fa-chart-column"></i> Dashboard</a> — 25+ gráficos em 5 categorias</li>
  <li><a href="analise_geografica.html"><i class="fa-solid fa-road"></i> Dashboard 1 — Rodovias</a> — visão por rodovia, tipo de evento e ano</li>
  <li><a href="analise_subtrechos.html"><i class="fa-solid fa-route"></i> Dashboard 2 — Subtrechos</a> — visão detalhada por subtrecho, tipo de evento e ano</li>
  <li><a href="RELATORIO_EXECUTIVO.html"><i class="fa-solid fa-file-lines"></i> Relatório Executivo</a> — síntese analítica com recomendações</li>
</ul></section>

<section><h2>Metodologia</h2>
<ol>
  <li><strong>Fonte:</strong> CSVs abertos do Infosiga SP (sinistros, pessoas e veículos), período {anos_range}.</li>
  <li><strong>Processamento:</strong> parse de datas, conversão de coordenadas (vírgula para ponto decimal), remoção de acentos, filtro pela <em>bounding box</em> do estado de São Paulo e derivação de flags (tem_vitima, tem_fatal, em_rodovia).</li>
  <li><strong>Análise geográfica:</strong> <em>spatial join</em> do tipo <em>nearest</em> (tolerância de 300 m) entre os pontos de sinistros e a Malha Rodoviária Estadual do DER/SP (EPSG:5880). A <strong>menor unidade espacial de análise é o subtrecho</strong>; as leituras por rodovia são agregações desse nível.</li>
  <li><strong>Ressalvas:</strong> os dados mais recentes são preliminares; a cobertura de geolocalização e o preenchimento do campo <code>administracao</code> variam conforme o órgão notificador.</li>
</ol></section>

<section><h2>Listagem de gráficos</h2>
<ol>
  <li>Total de sinistros por ano</li>
  <li>Óbitos por ano</li>
  <li>Vítimas por gravidade (empilhado)</li>
  <li>Modal / tipo de veículo envolvido</li>
  <li>Top 10 tipos de sinistro</li>
  <li>Gravidade por tipo de sinistro</li>
  <li>Gravidade da lesão (pessoas)</li>
  <li>Sexo das vítimas</li>
  <li>Faixa etária das vítimas</li>
  <li>Tipo de vítima</li>
  <li>Evolução anual de óbitos (pessoas)</li>
  <li>Óbitos por tipo de vítima</li>
  <li>Série temporal mensal</li>
  <li>Mapa de calor de sazonalidade</li>
  <li>Sinistros por dia da semana</li>
  <li>Óbitos por dia da semana</li>
  <li>Turno</li>
  <li>Distribuição horária</li>
  <li>Sinistros por região administrativa</li>
  <li>Óbitos por região administrativa</li>
  <li>Top 20 municípios em óbitos</li>
  <li>Sinistros por tipo de via</li>
  <li>Administração da via</li>
  <li>Heatmap dia × turno</li>
  <li>Letalidade por hora</li>
  <li>Letalidade anual</li>
  <li>Tempo sinistro → óbito</li>
  <li>Top 10 rodovias (sinistros)</li>
  <li>Top 10 rodovias (óbitos)</li>
  <li>Top 10 rodovias (densidade)</li>
  <li>Top 10 rodovias (letalidade)</li>
  <li>Bottom 10 rodovias</li>
  <li>Top 10 trechos (sinistros)</li>
  <li>Top 10 trechos (óbitos)</li>
  <li>Top 10 trechos (densidade)</li>
  <li>Top 10 trechos (óbitos/km)</li>
  <li>Trechos da rodovia campeã</li>
</ol></section>
</main>
"""
(DOCS / "GUIA_ACESSO.html").write_text(html_page("Guia — Infosiga SP", guia_body), encoding="utf-8")

print("Páginas geradas em:", DOCS)
for f in sorted(DOCS.glob("*.html")):
    print(" -", f.name, f.stat().st_size // 1024, "KB")
