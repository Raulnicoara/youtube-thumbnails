---
name: youtube-thumbnails
description: Designs YouTube thumbnails for free - researches competitor thumbnails, plans 4 click-worthy concepts (A/B/C/D), and builds them locally from the creator's real headshot, logos and bold text, then iterates on feedback. Use whenever someone wants to make, design, redo or brainstorm a YouTube thumbnail, gives a video title or topic and wants visuals for it, or wants thumbnail options to compare - even if they don't say "thumbnail".
---

# YouTube Thumbnails (free)

Everything here is free: no API keys, no paid services. Competitor research uses yt-dlp, you (Claude) analyse the images yourself, and thumbnails are rendered locally with Pillow from the creator's real headshot (background removed with rembg), so the face always looks exactly like them.

**Paths.** Scripts are in the `scripts/` folder of this skill's base directory (shown when the skill loads). In every command set `S` to that folder, e.g. `S="<skill base dir>/scripts"`. Always use `python3`.

**User data** lives in `~/youtube-thumbnails/` (override with `YT_THUMBS_HOME`) so it survives plugin updates:
- `headshots/` - creator photos, named by expression (`raul-surprised.jpg`, `raul-pointing.png`)
- `assets/` - logos, screenshots, product shots
- `brand_style_guide.md` - channel colors, fonts, style. Read it if it's filled in.

Output goes in the current working directory: `./thumbnails/<YYYY-MM-DD>-<topic-slug>/`.

Full spec format for the renderer: `reference.md` in this skill's base directory. Read it before writing your first spec.

---

## Step 0 - First run only

```bash
python3 "$S/setup.py"
```
If it lists missing packages, install them (`python3 -m pip install pillow yt-dlp "rembg[cpu]"`). It creates the data folders and downloads free fonts. The first background removal downloads a ~170 MB model once.

## Step 1 - Gather context

Ask, in one message:
1. What is the video about, and what's the title (or working title)?
2. Who is on the thumbnail? Put their photo(s) in `~/youtube-thumbnails/headshots/` (clear face, good light, any background). Different expressions help.
3. Any logos, screenshots or products to show? Put them in `~/youtube-thumbnails/assets/` and say which - or none.

Then `ls` both folders. With several headshots, pick the expression that fits the angle: surprised → shock/"you're doing it wrong"; pointing → tutorial; smiling → transformation/result; serious → authority.

## Step 2 - Cut out the headshot

```bash
python3 "$S/cutout.py" ~/youtube-thumbnails/headshots/<file>
```
Creates `<name>_cutout.png` next to it (reused next time). **Look at the cutout** (Read the PNG). If hair or shoulders are clipped badly, tell the user and ask for a photo with a plainer background. Logos with a solid background can be cut out the same way; transparent PNGs need nothing.

## Step 3 - Research the niche

```bash
OUT="thumbnails/<YYYY-MM-DD>-<topic-slug>"
python3 "$S/search_examples.py" "<video topic>" --output "$OUT/refs"
```
Saves up to 12 top thumbnails, `examples.json` (titles, channels, views) and `contact_sheet.jpg`. **Read `contact_sheet.jpg`** and write `$OUT/refs/analysis.md` covering:
- dominant colors (so we can contrast against them)
- text: how many words, phrasing patterns that are overused
- faces: how big, which emotions, where in frame
- composition patterns of the highest-view videos
- the gap: what nobody is doing that would stand out

If the search fails (no network, YouTube blocked), say so and either ask for 3-5 competitor video links or continue without research.

## Step 4 - Strategy: desire loop + 4 concepts

Show the user this table first:

| | |
|---|---|
| **Desire** - what does the viewer want? | |
| **Pain** - what's frustrating them now? | |
| **Solution** - what does the video deliver? | |
| **Curiosity gap** - what makes them need to click? | |

Then 4 genuinely different concepts, one per archetype:
- **A - Transformation**: before/after, the result
- **B - Shock**: "you're doing it wrong", bold claim, big emotion
- **C - Authority**: expert reveal, numbers, proof
- **D - Curiosity**: open loop, hidden thing, "nobody tells you this"

For each: one line on the idea, the exact on-image text, and the layout. Text rules: **max 4 words**, never repeat the title (the thumbnail and title work as a pair), one highlighted word.

## Step 5 - Build all 4

Write `$OUT/batch-1/A.json` ... `D.json` (format in `reference.md`), then:
```bash
B="$OUT/batch-1"
for c in A B C D; do python3 "$S/render_thumbnail.py" --spec "$B/$c.json" --output "$B/$c.png"; done
python3 "$S/combine_thumbnails.py" --inputs "$B/A.png" "$B/B.png" "$B/C.png" "$B/D.png" --output "$B/comparison.png"
```

**Check your own work before showing it.** Read each `*_small.png` (320×180, the size most people see on a phone) and fix anything that fails:
- text readable at small size? (if not: fewer words, bigger, stronger stroke)
- face large (roughly 50-75% of frame height) and expression visible?
- one clear focal point, nothing important under the bottom-right corner (YouTube puts the video length there)
- strong contrast with the niche colors from Step 3
- nothing touching the edges by accident, no overlapping text and arrows

Then show `comparison.png` with a one-line pitch per concept and ask which to develop.

## Step 6 - Iterate

Every new round goes in a new folder (`batch-2/`, `batch-3/`...) so A/B/C/D always mean the current round. Copy the chosen spec(s), change what the user asked, re-render, re-check, show the new grid. When one is final, tell the user the path to the 1280×720 PNG (ready to upload to YouTube).

---

## Optional: an AI-painted scene with the free Gemini app

The renderer can't paint new scenes (a person in a server room, holding a giant product...). If a concept needs one, offer this free manual step - **never** try to automate the Gemini website:

1. Write `$OUT/batch-N/gemini_prompts.md` with one paste-ready prompt per concept that needs it: scene, lighting, camera angle, mood, 16:9 aspect, and "leave empty space on the <left/right> for headline text; no text in the image". If the person should appear, say to attach their headshot and keep their face identical.
2. Tell the user: open gemini.google.com (free Google account), attach the headshot if needed, paste the prompt, download the image, save it as `A_gemini.png` (etc.) in that batch folder.
3. When they confirm, use it as the background: `{"type": "image", "path": ".../A_gemini.png"}`, and add the text, arrows and logos on top as usual.

Images from the free Gemini app carry a small visible watermark; mention it, and don't try to remove it.
