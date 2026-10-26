"""Render a 1280x720 YouTube thumbnail from a JSON spec. Free and fully local.

    python3 render_thumbnail.py --spec A.json --output A.png

Spec format (all coordinates in pixels on a 1280x720 canvas; see SKILL.md):
{
  "background": {"type": "gradient", "colors": ["#0b0f1a", "#1f2a44"], "angle": 135}
              | {"type": "radial", "colors": ["#3a1c71", "#000000"], "center": [900, 360]}
              | {"type": "solid", "color": "#111111"}
              | {"type": "image", "path": "bg.png", "blur": 0, "darken": 0.25},
  "glows": [{"x": 900, "y": 380, "radius": 380, "color": "#ff6a00", "opacity": 0.7}],
  "vignette": 0.45,
  "layers": [ person | image | text | arrow | shape ... drawn in order ]
}
"""
import argparse
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

from common import HEIGHT, WIDTH, font_path, hex_to_rgba


# ---------- helpers ----------

def place(canvas, img, x, y, anchor="top-left"):
    """Alpha-composite img onto canvas with (x, y) at the given anchor of img; clips at edges."""
    v, h = anchor.split("-") if "-" in anchor else ("center", "center")
    left = round(x - {"left": 0, "center": img.width / 2, "right": img.width}[h])
    top = round(y - {"top": 0, "center": img.height / 2, "bottom": img.height}[v])
    sx, sy = max(0, -left), max(0, -top)
    ex, ey = min(img.width, canvas.width - left), min(img.height, canvas.height - top)
    if ex > sx and ey > sy:
        canvas.alpha_composite(img.crop((sx, sy, ex, ey)), (left + sx, top + sy))


def outline_layer(img, width, color):
    """Solid silhouette of img grown by `width` px (sticker-style outline)."""
    pad = width * 2
    a = Image.new("L", (img.width + pad * 2, img.height + pad * 2), 0)
    a.paste(img.getchannel("A"), (pad, pad))
    grown = a.filter(ImageFilter.GaussianBlur(width / 2)).point(lambda v: 255 if v > 8 else 0)
    grown = grown.filter(ImageFilter.GaussianBlur(1))
    sil = Image.new("RGBA", a.size, hex_to_rgba(color))
    sil.putalpha(grown)
    return sil, pad


def glow_layer(img, radius, color, strength=1.0):
    pad = radius * 2
    a = Image.new("L", (img.width + pad * 2, img.height + pad * 2), 0)
    a.paste(img.getchannel("A"), (pad, pad))
    a = a.filter(ImageFilter.GaussianBlur(radius)).point(lambda v: min(255, int(v * 1.8 * strength)))
    g = Image.new("RGBA", a.size, hex_to_rgba(color))
    g.putalpha(a)
    return g, pad


def decorate(img, spec):
    """Add outline / glow / drop shadow around an RGBA image; returns the new image."""
    layers, pad = [], 0
    if spec.get("glow"):
        gl = spec["glow"]
        gl = gl if isinstance(gl, dict) else {"color": gl}
        g, p = glow_layer(img, gl.get("radius", 30), gl.get("color", "#ffffff"), gl.get("strength", 1.0))
        layers.append((g, p))
        pad = max(pad, p)
    if spec.get("shadow"):
        sh = spec["shadow"] if isinstance(spec["shadow"], dict) else {}
        r, off = sh.get("blur", 18), sh.get("offset", [8, 12])
        s, p = glow_layer(img, r, sh.get("color", "#000000"), sh.get("strength", 0.9))
        layers.append((s, p, tuple(off)))
        pad = max(pad, p + max(abs(off[0]), abs(off[1])))
    if spec.get("outline"):
        ol = spec["outline"]
        ol = ol if isinstance(ol, dict) else {"color": ol}
        o, p = outline_layer(img, ol.get("width", 8), ol.get("color", "#ffffff"))
        layers.append((o, p))
        pad = max(pad, p)
    if not layers:
        return img, 0
    out = Image.new("RGBA", (img.width + pad * 2, img.height + pad * 2), (0, 0, 0, 0))
    for item in layers:
        layer, p = item[0], item[1]
        off = item[2] if len(item) > 2 else (0, 0)
        out.alpha_composite(layer, (pad - p + off[0], pad - p + off[1]))
    out.alpha_composite(img, (pad, pad))
    return out, pad


def load_font(name, size):
    path = font_path(name)
    return ImageFont.truetype(path, size) if path else ImageFont.load_default()


# ---------- background ----------

def background(spec):
    kind = spec.get("type", "gradient")
    if kind == "solid":
        return Image.new("RGBA", (WIDTH, HEIGHT), hex_to_rgba(spec.get("color", "#111111")))
    if kind == "image":
        with Image.open(Path(spec["path"]).expanduser()) as im:
            im = ImageOps.fit(im.convert("RGBA"), (WIDTH, HEIGHT), Image.LANCZOS,
                              centering=tuple(spec.get("focus", [0.5, 0.5])))
        if spec.get("blur"):
            im = im.filter(ImageFilter.GaussianBlur(spec["blur"]))
        if spec.get("saturation") is not None:
            im = ImageEnhance.Color(im).enhance(spec["saturation"])
        if spec.get("darken"):
            im = Image.blend(im, Image.new("RGBA", im.size, (0, 0, 0, 255)), spec["darken"])
        return im
    colors = [hex_to_rgba(c) for c in spec.get("colors", ["#0b0f1a", "#1f2a44"])]
    if kind == "radial":
        cx, cy = spec.get("center", [WIDTH / 2, HEIGHT / 2])
        maxd = math.hypot(max(cx, WIDTH - cx), max(cy, HEIGHT - cy))
        small = Image.new("L", (WIDTH // 4, HEIGHT // 4))
        small.putdata([min(255, int(255 * math.hypot(x * 4 - cx, y * 4 - cy) / maxd))
                       for y in range(small.height) for x in range(small.width)])
        t = small.resize((WIDTH, HEIGHT), Image.BILINEAR)
    else:
        ang = math.radians(spec.get("angle", 135))
        dx, dy = math.cos(ang), math.sin(ang)
        span = abs(WIDTH * dx) + abs(HEIGHT * dy)
        small = Image.new("L", (WIDTH // 4, HEIGHT // 4))
        small.putdata([max(0, min(255, int(255 * (((x * 4 - WIDTH / 2) * dx + (y * 4 - HEIGHT / 2) * dy) / span + 0.5))))
                       for y in range(small.height) for x in range(small.width)])
        t = small.resize((WIDTH, HEIGHT), Image.BILINEAR)
    # Multi-stop gradient: blend consecutive color pairs over equal segments of t.
    out = Image.new("RGBA", (WIDTH, HEIGHT), colors[0])
    n = len(colors) - 1
    for i in range(n):
        lo, hi = 255 * i / n, 255 * (i + 1) / n
        mask = t.point(lambda v, lo=lo, hi=hi: 0 if v <= lo else 255 if v >= hi else int(255 * (v - lo) / (hi - lo)))
        out = Image.composite(Image.new("RGBA", out.size, colors[i + 1]), out, mask)
    return out


def add_glow(canvas, g):
    r = g.get("radius", 300)
    # Generous margin so the blur fades to zero before the edge of the blob image.
    blob = Image.new("L", (r * 3, r * 3), 0)
    ImageDraw.Draw(blob).ellipse((r, r, r * 2, r * 2), fill=int(255 * g.get("opacity", 0.6)))
    blob = blob.filter(ImageFilter.GaussianBlur(r * 0.3))
    layer = Image.new("RGBA", blob.size, hex_to_rgba(g.get("color", "#ffffff")))
    layer.putalpha(blob)
    place(canvas, layer, g.get("x", WIDTH / 2), g.get("y", HEIGHT / 2), "center")


def add_vignette(canvas, strength):
    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    ImageDraw.Draw(mask).ellipse((-WIDTH * 0.15, -HEIGHT * 0.25, WIDTH * 1.15, HEIGHT * 1.25), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(160))
    dark = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    dark.putalpha(ImageChops.invert(mask).point(lambda v: int(v * strength)))
    canvas.alpha_composite(dark)


# ---------- layers ----------

def layer_image(canvas, spec):
    with Image.open(Path(spec["path"]).expanduser()) as im:
        img = im.convert("RGBA")
    if spec.get("crop"):  # [left, top, right, bottom] in source pixels
        img = img.crop(tuple(spec["crop"]))
    if spec.get("height"):
        img = img.resize((max(1, round(img.width * spec["height"] / img.height)), round(spec["height"])), Image.LANCZOS)
    elif spec.get("width"):
        img = img.resize((round(spec["width"]), max(1, round(img.height * spec["width"] / img.width))), Image.LANCZOS)
    if spec.get("flip"):
        img = ImageOps.mirror(img)
    if spec.get("brightness"):
        img = ImageEnhance.Brightness(img).enhance(spec["brightness"])
    if spec.get("contrast"):
        img = ImageEnhance.Contrast(img).enhance(spec["contrast"])
    if spec.get("saturation"):
        img = ImageEnhance.Color(img).enhance(spec["saturation"])
    if spec.get("rim_light"):
        img = rim_light(img, spec["rim_light"])
    img, pad = decorate(img, spec)
    if spec.get("rotate"):
        img = img.rotate(spec["rotate"], resample=Image.BICUBIC, expand=True)
    anchor = spec.get("anchor", "bottom-center" if spec["type"] == "person" else "top-left")
    x, y = spec.get("x", WIDTH / 2), spec.get("y", HEIGHT)
    # Shift by the decoration padding so x/y still refer to the original image edge.
    v, h = anchor.split("-") if "-" in anchor else ("center", "center")
    x += {"left": -pad, "center": 0, "right": pad}[h]
    y += {"top": -pad, "center": 0, "bottom": pad}[v]
    place(canvas, img, x, y, anchor)


def rim_light(img, spec):
    """Coloured edge light on one side of a cutout, so a person sits in the scene."""
    spec = spec if isinstance(spec, dict) else {"color": spec}
    side = spec.get("side", "left")
    a = img.getchannel("A")
    shift = {"left": (12, 0), "right": (-12, 0), "top": (0, 12)}[side]
    inner = ImageChops.offset(a, *shift)
    edge = ImageChops.subtract(a, inner).filter(ImageFilter.GaussianBlur(4))
    edge = edge.point(lambda v: min(255, int(v * spec.get("strength", 1.6))))
    light = Image.new("RGBA", img.size, hex_to_rgba(spec.get("color", "#ffffff")))
    light.putalpha(ImageChops.multiply(edge, a))
    out = img.copy()
    out.alpha_composite(light)
    return out


def layer_text(canvas, spec):
    font = load_font(spec.get("font", "anton"), spec.get("size", 120))
    text = spec["text"].upper() if spec.get("uppercase", True) else spec["text"]
    color = hex_to_rgba(spec.get("color", "#ffffff"))
    highlights = {w.upper() if spec.get("uppercase", True) else w: hex_to_rgba(c)
                  for w, c in (spec.get("highlight") or {}).items()}
    stroke = spec.get("stroke", {"color": "#000000", "width": max(4, spec.get("size", 120) // 14)})
    sw = stroke.get("width", 0) if stroke else 0
    scol = hex_to_rgba(stroke.get("color", "#000000")) if stroke else None

    # Shrink to fit max_width if requested.
    max_w = spec.get("max_width")
    lines = text.split("\n")
    if max_w:
        size = spec.get("size", 120)
        while size > 20 and max(font.getlength(l) for l in lines) + sw * 2 > max_w:
            size -= 4
            font = load_font(spec.get("font", "anton"), size)
    asc, desc = font.getmetrics()
    line_h = int((asc + desc) * spec.get("line_spacing", 0.95))
    widths = [font.getlength(l) for l in lines]
    block_w = int(max(widths)) + sw * 2
    block_h = line_h * (len(lines) - 1) + asc + desc + sw * 2

    box = spec.get("box")
    bp = box.get("padding", 18) if box else 0
    img = Image.new("RGBA", (block_w + bp * 2, block_h + bp * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if box:
        d.rounded_rectangle((0, 0, img.width - 1, img.height - 1), radius=box.get("radius", 12),
                            fill=hex_to_rgba(box.get("color", "#e50914")))
    align = spec.get("align", "left")
    space = font.getlength(" ")
    for i, line in enumerate(lines):
        lx = bp + sw + {"left": 0, "center": (block_w - sw * 2 - widths[i]) / 2,
                        "right": block_w - sw * 2 - widths[i]}[align]
        ly = bp + sw + i * line_h
        for word in line.split(" "):
            key = word.strip(".,!?:;\"'")
            d.text((lx, ly), word, font=font, fill=highlights.get(key, color),
                   stroke_width=sw, stroke_fill=scol)
            lx += font.getlength(word) + space

    img, _ = decorate(img, {k: spec[k] for k in ("shadow", "glow") if k in spec})
    if spec.get("rotate"):
        img = img.rotate(spec["rotate"], resample=Image.BICUBIC, expand=True)
    place(canvas, img, spec.get("x", 60), spec.get("y", 60), spec.get("anchor", "top-left"))


def layer_arrow(canvas, spec):
    (x1, y1), (x2, y2) = spec["from"], spec["to"]
    w = spec.get("width", 18)
    bend = spec.get("curve", 0)  # px offset of the control point, + bends one way, - the other
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    length = math.hypot(x2 - x1, y2 - y1) or 1
    cx, cy = mx - (y2 - y1) / length * bend, my + (x2 - x1) / length * bend
    pts = [((1 - t) ** 2 * x1 + 2 * (1 - t) * t * cx + t * t * x2,
            (1 - t) ** 2 * y1 + 2 * (1 - t) * t * cy + t * t * y2) for t in [i / 40 for i in range(41)]]
    ang = math.atan2(y2 - pts[-4][1], x2 - pts[-4][0])
    head = w * 2.6
    tip = (x2, y2)
    left = (x2 - head * math.cos(ang - 0.5), y2 - head * math.sin(ang - 0.5))
    right = (x2 - head * math.cos(ang + 0.5), y2 - head * math.sin(ang + 0.5))
    shaft_end = len(pts) - 1
    while shaft_end > 1 and math.hypot(pts[shaft_end][0] - x2, pts[shaft_end][1] - y2) < head * 0.7:
        shaft_end -= 1
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    ol = spec.get("outline", {"color": "#000000", "width": 6})
    passes = [(hex_to_rgba(ol["color"]), ol.get("width", 6))] if ol else []
    passes.append((hex_to_rgba(spec.get("color", "#ff2d2d")), 0))
    for col, extra in passes:
        d.line(pts[:shaft_end + 1], fill=col, width=w + extra * 2, joint="curve")
        r = (w + extra * 2) / 2
        d.ellipse((x1 - r, y1 - r, x1 + r, y1 + r), fill=col)
        if extra:
            d.polygon([tip, left, right], fill=col, outline=col, width=extra * 2)
        else:
            d.polygon([tip, left, right], fill=col)
    canvas.alpha_composite(layer)


def layer_shape(canvas, spec):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    box = tuple(spec["box"])  # [left, top, right, bottom]
    fill = hex_to_rgba(spec["fill"], int(255 * spec.get("opacity", 1))) if spec.get("fill") else None
    ol = spec.get("outline")
    kw = {"fill": fill}
    if ol:
        kw.update(outline=hex_to_rgba(ol.get("color", "#ffffff")), width=ol.get("width", 6))
    if spec.get("shape", "rect") == "ellipse":
        d.ellipse(box, **kw)
    else:
        d.rounded_rectangle(box, radius=spec.get("radius", 0), **kw)
    if spec.get("rotate"):
        layer = layer.rotate(spec["rotate"], center=((box[0] + box[2]) / 2, (box[1] + box[3]) / 2),
                             resample=Image.BICUBIC)
    canvas.alpha_composite(layer)


LAYERS = {"person": layer_image, "image": layer_image, "text": layer_text,
          "arrow": layer_arrow, "shape": layer_shape}


def render(spec):
    canvas = background(spec.get("background", {}))
    for g in spec.get("glows", []):
        add_glow(canvas, g)
    if spec.get("vignette"):
        add_vignette(canvas, spec["vignette"])
    for layer in spec.get("layers", []):
        fn = LAYERS.get(layer.get("type"))
        if not fn:
            sys.exit(f"Unknown layer type: {layer.get('type')}")
        fn(canvas, layer)
    return canvas.convert("RGB")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--spec", required=True, help="JSON spec file")
    p.add_argument("--output", required=True, help="output .png")
    args = p.parse_args()
    spec = json.loads(Path(args.spec).read_text())
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    img = render(spec)
    img.save(out)
    # Phone-size preview: most viewers see the thumbnail this small.
    img.resize((320, 180), Image.LANCZOS).save(out.with_name(out.stem + "_small.png"))
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
