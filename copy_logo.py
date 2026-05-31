import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEST = ROOT / "logo-trivago-food.png"
ASSETS = Path(
    r"C:\Users\zdksg\.cursor\projects\c-Users-zdksg-Downloads-trabalho-facul\assets"
)

if DEST.is_file() and DEST.stat().st_size > 500:
    sys.exit(0)

if ASSETS.is_dir():
    pngs = sorted(ASSETS.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
    if pngs:
        shutil.copy2(pngs[0], DEST)
        print("Logo copiada:", DEST.name)
