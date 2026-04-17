# Acidentes InfoSiga - Análise Exploratória

Pipeline de análise exploratória dos dados de sinistros de trânsito do estado de São Paulo (InfoSiga-SP), com geração de dashboards HTML interativos.

## Estrutura

```
analise/
  01_processa_dados.py      # ETL e consolidação dos CSVs do InfoSiga
  02_analise_geografica.py  # Cruzamento espacial com a malha rodoviária
  03_gera_html.py           # Geração dos dashboards HTML
  serve.py                  # Servidor HTTP local para visualizar os dashboards
  requirements.txt
docs/                       # Dashboards HTML publicáveis (GitHub Pages)
dados/                      # (ignorado) CSVs brutos do InfoSiga + shapefile da malha
analise/out/                # (ignorado) artefatos intermediários gerados pelo pipeline
```

## Requisitos

- Python 3.11+
- Dependências em [analise/requirements.txt](analise/requirements.txt)

## Como executar

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r analise/requirements.txt

python analise/01_processa_dados.py
python analise/02_analise_geografica.py
python analise/03_gera_html.py

python analise/serve.py 8765
```

Abra http://localhost:8765/index.html no navegador.

## Dados de entrada

A pasta `dados/` não é versionada. É necessário baixar:
- CSVs do InfoSiga-SP (pessoas, sinistros, veículos) em `dados/dados_infosiga/`
- Shapefile da Malha Rodoviária Estadual em `dados/Sistema Rodoviário Estadual/`
