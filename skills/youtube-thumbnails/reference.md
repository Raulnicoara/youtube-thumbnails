# Thumbnail spec reference

`render_thumbnail.py` draws a 1280×720 PNG from a JSON spec. Coordinates are pixels on that canvas (x right, y down). Colors are hex (`"#ff2d2d"`, `"#ff2d2d80"` with alpha). Relative paths are relative to where you run the command, so absolute paths or `~/...` are safest.

## Top level

```json
{
  "background": { ... },
  "glows": [ {"x": 900, "y": 380, "radius": 380, "color": "#ff6a00", "opacity": 0.7} ],
  "vignette": 0.45,
  "layers": [ ... drawn in order, later on top ... ]
}
```
- `glows`: soft colored light blobs, great behind a person or logo.
- `vignette`: 0-1, darkens the edges to pull the eye to the center.

## Backgrounds

| type | fields |
|---|---|
| `gradient` | `colors` (2+), `angle` in degrees (0 = left→right, 90 = top→bottom, default 135) |
| `radial` | `colors` (center → edge), `center` [x, y] |
| `solid` | `color` |
| `image` | `path`, optional `blur` (px), `darken` (0-1), `saturation` (1 = unchanged), `focus` [0-1, 0-1] crop center |

## Layers

### `person` / `image`
```json
{"type": "person", "path": "~/youtube-thumbnails/headshots/raul-surprised_cutout.png",
 "x": 940, "y": 720, "height": 680, "anchor": "bottom-center",
 "outline": {"color": "#ffffff", "width": 10}, "shadow": true,
 "glow": {"color": "#ff8a00", "radius": 40}, "rim_light": {"color": "#ff9a3c", "side": "left"},
 "flip": false, "rotate": 0, "brightness": 1.05, "contrast": 1.1, "saturation": 1.1}
```
- Size with `height` **or** `width`. `crop` [l, t, r, b] crops the source first (e.g. a screenshot).
- `anchor`: which point of the image sits at (x, y): `top-left`, `top-center`, `top-right`, `center-left`, `center`, `center-right`, `bottom-left`, `bottom-center` (default for `person`), `bottom-right`. Default for `image` is `top-left`.
- `outline`: sticker-style border (string color or `{color, width}`). White or brand color separates a face from busy backgrounds.
- `shadow`: `true` or `{"blur": 18, "offset": [8, 12], "color": "#000000", "strength": 0.9}`.
- `glow`: string color or `{color, radius, strength}`.
- `rim_light`: colored edge light on one `side` (`left`/`right`/`top`) so the person matches a colored glow.
- `flip`: mirror, so the person faces into the frame toward the text.
- People usually sit at the bottom edge (`y: 720`, `anchor: bottom-center`), cropped at chest height. Let the head go large.

### `text`
```json
{"type": "text", "text": "STOP CODING\nLIKE THIS", "x": 60, "y": 90, "size": 150,
 "font": "anton", "color": "#ffffff", "highlight": {"THIS": "#ffd400"},
 "stroke": {"color": "#000000", "width": 10}, "shadow": true,
 "box": {"color": "#e50914", "padding": 16, "radius": 12},
 "max_width": 620, "align": "left", "line_spacing": 0.95, "rotate": -3, "anchor": "top-left"}
```
- `\n` for line breaks. Uppercased unless `"uppercase": false`.
- `font`: `anton` (tall condensed, default), `bebas` (thin condensed), `archivo-black` (wide heavy), `bangers` (comic), or a path to a .ttf/.otf. Falls back to a heavy system font if offline.
- `highlight`: word → color, to make one word pop.
- `stroke`: outline (default black, ~size/14). `null` for none.
- `box`: a colored label behind the text.
- `max_width`: shrinks the size until the widest line fits.
- `glow` works on text too.

### `arrow`
```json
{"type": "arrow", "from": [560, 600], "to": [760, 470], "curve": -60,
 "color": "#ffd400", "width": 16, "outline": {"color": "#000000", "width": 6}}
```
`curve` bends it (px, either sign). `outline: null` for none.

### `shape`
```json
{"type": "shape", "shape": "rect", "box": [40, 500, 600, 680], "fill": "#000000", "opacity": 0.6,
 "radius": 20, "outline": {"color": "#ffffff", "width": 6}, "rotate": 0}
```
`shape`: `rect` or `ellipse` (e.g. a red circle around something). Omit `fill` for an outline only.

## Proven layouts

- **Face right, text left**: person `x≈930, y=720, height≈650`; text `x=60, y≈90, max_width≈620`; glow behind the head.
- **Before / after split**: two `shape` rects (left gray/desaturated, right bright), a big arrow across the middle, a 1-2 word label on each side.
- **Big number**: one huge number (`size` 260-320) with a box, the face reacting next to it.
- **Logo reveal**: logo large with glow at center-right, person pointing at it from the left (`flip` if needed).
- **Circle the thing**: screenshot as an `image` layer + red `ellipse` outline + arrow + shocked face.

Keep the bottom-right corner (about x > 1100, y > 640) free of anything important: YouTube's duration badge covers it.
