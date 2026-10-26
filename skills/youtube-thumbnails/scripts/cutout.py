"""Remove the background from a headshot so it can be placed on any thumbnail.

Free and local (rembg). The first run downloads a ~170 MB model once.
Output: <name>_cutout.png next to the headshot; reused if it already exists.

    python3 cutout.py ~/youtube-thumbnails/headshots/raul-surprised.jpg
"""
import argparse
import sys
from pathlib import Path

from PIL import Image


def cutout(src, force=False):
    src = Path(src).expanduser()
    dest = src.with_name(f"{src.stem}_cutout.png")
    if dest.exists() and not force:
        return dest
    try:
        from rembg import new_session, remove
    except ImportError:
        sys.exit('rembg is not installed. Run: python3 -m pip install "rembg[cpu]"')

    with Image.open(src) as im:
        im = im.convert("RGB")
        # Keep processing quick while preserving enough detail for a 720px-tall frame.
        if max(im.size) > 2000:
            im.thumbnail((2000, 2000))
        out = remove(im, session=new_session("isnet-general-use"), post_process_mask=True)
    bbox = out.getchannel("A").point(lambda a: 255 if a > 20 else 0).getbbox()
    if bbox:
        out = out.crop(bbox)
    out.save(dest)
    return dest


def main():
    p = argparse.ArgumentParser()
    p.add_argument("images", nargs="+")
    p.add_argument("--force", action="store_true", help="redo even if a cutout exists")
    args = p.parse_args()
    for img in args.images:
        print(f"Saved: {cutout(img, args.force)}")


if __name__ == "__main__":
    main()
