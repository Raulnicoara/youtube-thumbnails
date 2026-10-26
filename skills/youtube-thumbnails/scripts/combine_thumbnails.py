"""Put up to four thumbnails in a labelled 2x2 grid for side-by-side comparison.

    python3 combine_thumbnails.py --inputs A.png B.png C.png D.png --output comparison.png
"""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from common import font_path

TW, TH, GAP = 960, 540, 24


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--inputs", nargs="+", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--labels", nargs="*", help="defaults to A, B, C, D")
    args = p.parse_args()

    labels = args.labels or [chr(65 + i) for i in range(len(args.inputs))]
    cols = 2 if len(args.inputs) > 1 else 1
    rows = (len(args.inputs) + cols - 1) // cols
    grid = Image.new("RGB", (cols * TW + (cols + 1) * GAP, rows * TH + (rows + 1) * GAP), "#1b1b1b")
    fp = font_path("anton")
    font = ImageFont.truetype(fp, 64) if fp else ImageFont.load_default()
    d = ImageDraw.Draw(grid)
    for i, path in enumerate(args.inputs):
        x = GAP + (i % cols) * (TW + GAP)
        y = GAP + (i // cols) * (TH + GAP)
        with Image.open(path) as im:
            grid.paste(im.convert("RGB").resize((TW, TH), Image.LANCZOS), (x, y))
        d.rounded_rectangle((x + 14, y + 14, x + 104, y + 104), radius=14, fill="#ffd400")
        d.text((x + 59, y + 59), labels[i], font=font, fill="black", anchor="mm")
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    grid.save(args.output)
    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()
