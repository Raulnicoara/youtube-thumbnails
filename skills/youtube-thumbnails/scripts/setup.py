"""One-time setup: create the data folders, copy the brand guide template, fetch fonts,
and report which free dependencies are missing."""
import importlib.util
import shutil

from common import (ASSETS_DIR, BRAND_GUIDE, DATA_DIR, FONT_SOURCES, HEADSHOTS_DIR,
                    SKILL_DIR, font_path)


def main():
    for d in (HEADSHOTS_DIR, ASSETS_DIR):
        d.mkdir(parents=True, exist_ok=True)
    if not BRAND_GUIDE.exists():
        shutil.copy(SKILL_DIR / "brand_style_guide.md", BRAND_GUIDE)
    for name in FONT_SOURCES:
        print(f"font {name}: {font_path(name)}")

    missing = [pkg for mod, pkg in (("PIL", "pillow"), ("yt_dlp", "yt-dlp"), ("rembg", "rembg[cpu]"))
               if importlib.util.find_spec(mod) is None]
    print(f"\nData folder: {DATA_DIR}")
    print(f"  headshots -> {HEADSHOTS_DIR}")
    print(f"  logos     -> {ASSETS_DIR}")
    print(f"  brand     -> {BRAND_GUIDE}")
    if missing:
        print("\nMISSING packages. Install with:\n  python3 -m pip install " + " ".join(f'"{m}"' for m in missing))
    else:
        print("\nAll dependencies installed.")


if __name__ == "__main__":
    main()
