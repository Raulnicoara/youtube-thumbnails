"""Find top YouTube videos for a topic and save their thumbnails plus a contact sheet.

Free: uses yt-dlp's YouTube search (no API key) and YouTube's public thumbnail URLs.
Claude then looks at contact_sheet.png itself to analyse the niche.

    python3 search_examples.py "claude code tutorial" --output workspace/.../refs
"""
import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from common import download, ui_font_path


def search(query, count):
    import yt_dlp

    opts = {"quiet": True, "skip_download": True, "extract_flat": True, "no_warnings": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(f"ytsearch{count * 2}:{query}", download=False)
    videos = []
    for e in info.get("entries") or []:
        vid = e.get("id")
        # Skip Shorts: their vertical thumbnails are not useful references.
        if not vid or "/shorts/" in (e.get("url") or ""):
            continue
        videos.append({
            "id": vid,
            "title": e.get("title") or "",
            "channel": e.get("channel") or e.get("uploader") or "",
            "views": e.get("view_count"),
            "duration": e.get("duration"),
            "url": f"https://www.youtube.com/watch?v={vid}",
        })
        if len(videos) >= count:
            break
    return videos


def fetch_thumb(vid, dest):
    for name in ("maxresdefault.jpg", "sddefault.jpg", "hqdefault.jpg"):
        try:
            download(f"https://i.ytimg.com/vi/{vid}/{name}", dest)
            with Image.open(dest) as im:
                if im.width > 200:  # maxres returns a 120px placeholder when missing
                    return True
        except Exception:
            continue
    return False


def fmt_views(n):
    if not n:
        return "? views"
    for div, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if n >= div:
            return f"{n / div:.1f}{suffix} views"
    return f"{n} views"


def contact_sheet(videos, out_path, cols=3):
    tw, th, cap = 480, 270, 54
    rows = (len(videos) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * (th + cap)), "white")
    draw = ImageDraw.Draw(sheet)
    fp = ui_font_path()
    try:
        small = ImageFont.truetype(fp, 16) if fp else ImageFont.load_default()
    except Exception:
        small = ImageFont.load_default()
    for i, v in enumerate(videos):
        x, y = (i % cols) * tw, (i // cols) * (th + cap)
        with Image.open(v["thumb"]) as im:
            im = im.convert("RGB")
            ratio = max(tw / im.width, th / im.height)
            im = im.resize((round(im.width * ratio), round(im.height * ratio)))
            left, top = (im.width - tw) // 2, (im.height - th) // 2
            sheet.paste(im.crop((left, top, left + tw, top + th)), (x, y))
        draw.text((x + 6, y + th + 4), f"#{i + 1} {v['title'][:52]}", fill="black", font=small)
        draw.text((x + 6, y + th + 26), f"{v['channel'][:30]} · {fmt_views(v['views'])}", fill="#555", font=small)
    sheet.save(out_path, quality=90)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("query")
    p.add_argument("--output", required=True)
    p.add_argument("--count", type=int, default=12)
    args = p.parse_args()

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    try:
        videos = search(args.query, args.count)
    except Exception as e:
        sys.exit(f"YouTube search failed: {e}\nTip: update yt-dlp (python3 -m pip install -U yt-dlp) "
                 "or paste video links and use --urls mode later.")

    kept = []
    for i, v in enumerate(videos, 1):
        dest = out / f"{i:02d}_{v['id']}.jpg"
        if fetch_thumb(v["id"], dest):
            v["thumb"] = str(dest)
            kept.append(v)
    if not kept:
        sys.exit("No thumbnails could be downloaded.")

    kept.sort(key=lambda v: v["views"] or 0, reverse=True)
    (out / "examples.json").write_text(json.dumps(kept, indent=2))
    contact_sheet(kept, out / "contact_sheet.jpg")
    for i, v in enumerate(kept, 1):
        print(f"#{i:2d} {fmt_views(v['views']):>12}  {v['title']}  ({v['channel']})")
    print(f"\nSaved {len(kept)} thumbnails + contact_sheet.jpg to {out}")


if __name__ == "__main__":
    main()
