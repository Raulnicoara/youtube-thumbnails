"""Shared paths and helpers for the YouTube thumbnail skill.

User data (headshots, logos, brand guide, fonts) lives outside the plugin so it
survives plugin updates. Override the location with YT_THUMBS_HOME.
"""
import functools
import os
import sys
import urllib.request
from pathlib import Path

DATA_DIR = Path(os.environ.get("YT_THUMBS_HOME", Path.home() / "youtube-thumbnails"))
HEADSHOTS_DIR = DATA_DIR / "headshots"
ASSETS_DIR = DATA_DIR / "assets"
FONTS_DIR = DATA_DIR / "fonts"
BRAND_GUIDE = DATA_DIR / "brand_style_guide.md"

SKILL_DIR = Path(__file__).resolve().parent.parent
WIDTH, HEIGHT = 1280, 720

# Free fonts (SIL Open Font License) fetched from the Google Fonts repo on first use.
FONT_SOURCES = {
    "anton": "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf",
    "bebas": "https://github.com/google/fonts/raw/main/ofl/bebasneue/BebasNeue-Regular.ttf",
    "archivo-black": "https://github.com/google/fonts/raw/main/ofl/archivoblack/ArchivoBlack-Regular.ttf",
    "bangers": "https://github.com/google/fonts/raw/main/ofl/bangers/Bangers-Regular.ttf",
}

# Heavy system fonts to fall back on when a download is not possible.
SYSTEM_FALLBACKS = [
    "C:/Windows/Fonts/impact.ttf",
    "C:/Windows/Fonts/ariblk.ttf",
    "/System/Library/Fonts/Supplemental/Impact.ttf",
    "/System/Library/Fonts/Supplemental/Arial Black.ttf",
    "/Library/Fonts/Impact.ttf",
    "/usr/share/fonts/truetype/msttcorefonts/Impact.ttf",
    "/usr/share/fonts/opentype/inter/Inter-Black.otf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def download(url, dest, timeout=30):
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
    dest.write_bytes(data)
    return dest


@functools.lru_cache(maxsize=None)
def font_path(name="anton"):
    """Return a usable font file for `name` (a key of FONT_SOURCES or a file path)."""
    if name and Path(name).expanduser().is_file():
        return str(Path(name).expanduser())
    key = (name or "anton").lower()
    if key in FONT_SOURCES:
        local = FONTS_DIR / Path(FONT_SOURCES[key]).name
        if not local.exists():
            try:
                download(FONT_SOURCES[key], local)
            except Exception as e:
                print(f"  ! could not download font '{key}' ({e}); using a system font", file=sys.stderr)
        if local.exists():
            return str(local)
    for path in SYSTEM_FALLBACKS:
        if Path(path).exists():
            return path
    return None


def hex_to_rgba(value, alpha=255):
    if isinstance(value, (list, tuple)):
        return tuple(value) if len(value) == 4 else (*value, alpha)
    v = value.lstrip("#")
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    r, g, b = int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16)
    a = int(v[6:8], 16) if len(v) == 8 else alpha
    return (r, g, b, a)


UI_FONTS = [
    "C:/Windows/Fonts/arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]


def ui_font_path():
    """A plain, readable font for captions on reference sheets."""
    return next((p for p in UI_FONTS if Path(p).exists()), None)
