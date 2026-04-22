"""Injeta o campo Municipio nas features da malha em rodovias_dashboard_main.json
sem precisar regenerar todo o pipeline. Idempotente.

Tambem regenera as versoes precompressed (.gz / .br) para garantir que o
servidor nao sirva conteudo desatualizado quando elas existirem.
"""
import gzip
import json
from pathlib import Path
import geopandas as gpd

ROOT = Path(__file__).resolve().parent.parent
SHP = ROOT / "dados" / "Sistema Rodoviário Estadual" / "MALHA_RODOVIARIA.shp"
JSON_PATH = ROOT / "docs" / "assets" / "geo" / "rodovias_dashboard_main.json"

gdf = gpd.read_file(SHP)
mun_by_sub = dict(zip(gdf["Subtrecho"].astype(str), gdf["Municipio"].astype(str)))

data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
features = data.get("malha", {}).get("features", [])

n_set = 0
for f in features:
    sub = str(f.get("properties", {}).get("Subtrecho") or "")
    mun = mun_by_sub.get(sub)
    if mun:
        f["properties"]["Municipio"] = mun
        n_set += 1

raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
JSON_PATH.write_bytes(raw)
print(f"Updated {n_set}/{len(features)} features with Municipio")

# Regenera precompressed .gz se existir, para nao servir conteudo antigo.
gz_path = JSON_PATH.with_suffix(JSON_PATH.suffix + ".gz")
if gz_path.exists():
    gz_path.write_bytes(gzip.compress(raw, compresslevel=6))
    print(f"Regenerated {gz_path.name} ({gz_path.stat().st_size} bytes)")

br_path = JSON_PATH.with_suffix(JSON_PATH.suffix + ".br")
if br_path.exists():
    try:
        import brotli  # type: ignore
        br_path.write_bytes(brotli.compress(raw, quality=6))
        print(f"Regenerated {br_path.name} ({br_path.stat().st_size} bytes)")
    except ImportError:
        br_path.unlink()
        print(f"Removed stale {br_path.name} (brotli nao instalado)")
