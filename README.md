# YouTube Thumbnails plugin

Free YouTube thumbnail designer for Claude. Ask Claude for a thumbnail and it will:

1. Ask for the video topic, your headshot and any logos
2. Remove the photo background (locally, free)
3. Pull the top thumbnails in your niche from YouTube and analyse them
4. Plan 4 different concepts (transformation, shock, authority, curiosity)
5. Render them at 1280×720, check them at phone size, and show a 2×2 comparison
6. Revise until you're happy

No API keys, no subscriptions. Needs Python 3 with `pillow`, `yt-dlp` and `rembg[cpu]` (Claude installs them on first run).

Your photos, logos and brand guide live in `~/youtube-thumbnails/`. Optional: Claude can write prompts for the free Gemini app if a concept needs an AI-painted scene; you paste them in yourself.

Inspired by the workflow in bwells271/AI-Automation-Network (Youtube-Thumbnail-Skill branch), rebuilt to run without paid APIs.
