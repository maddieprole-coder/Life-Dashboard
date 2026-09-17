# Safe Manual Handling for Cleaners — video generator

Renders the 3-minute training animation described in the technical video
generation specification, as a procedurally-drawn Python pipeline (no
external art or motion-graphics assets required).

## How the spec maps to code

The specification's JSON sections are kept as data, not re-typed into
Python, so the renderer is provably reading the same numbers the spec
gives:

| Spec section | File |
|---|---|
| 1. Video metadata | `spec/metadata.json` |
| 2. Color palette | `spec/colors.json` |
| 3. Scene structure (`SCENE_ARRAY`) | `spec/scenes.json` |
| 4. Character definition | `character.py` (dimensions/colours), `animations.py` (keyframes) |
| 5. Object definitions | `objects.py` |
| 6. Animation functions (pseudocode) | `animations.py`, `render.py` (implemented as real code) |
| 7. Audio specification | `audio.py` |

`render.py` is a generic interpreter: for a given global frame number it
finds the active scene in `spec/scenes.json`, then dispatches every live
element (`character`, `object`, `text_title`, `icon`, `split_screen`, ...)
to a drawing function using that element's own position/colour/timing
fields. Nothing about scene content is hardcoded outside the JSON.

The character is a procedural capsule/circle rig (`character.py`) rather
than hand-drawn artwork — simple geometric shapes, styled to match a
reference mascot image the project owner supplied: brown ponytail, white
t-shirt under blue denim overalls, yellow rubber gloves and sneakers, and
a broom/wheeled cleaning cart as props (`objects.py`). It no longer uses
the original spec text's hard hat / hi-vis vest outfit, per that later
direction.

## Running it

```bash
pip install -r requirements.txt

# Full 180s render at 1920x1080/24fps (matches spec exactly)
python3 generate_video.py

# Fast low-res smoke test
python3 generate_video.py --preview

# Render just one scene, e.g. scene 1 (0-20s)
python3 generate_video.py --start 0 --end 20 --output output/scene1.mp4
```

Output defaults to `output/safe_manual_handling.mp4`, matching the spec's
`mp4` / `h264` / `aac` / `1920x1080` / `24fps` / `8000k` video and `128k`
audio settings from `spec/metadata.json`.

## Audio

Sound effects (whooshes, dings, buzzers, footsteps, chimes) are
synthesized on the fly in `audio.py` from the `sound_effects` entries in
`spec/scenes.json` — no external SFX library is needed.

**Voiceover and background music are not fabricated.** This environment
has no licensed music library or TTS engine, and synthesizing "music" or
narration procedurally would produce something unusable for real
training. Instead:

- Drop a real voiceover recording at `audio_assets/voiceover_scene_N.mp3`
  for each scene (the spec already gives each scene's narration script in
  `scenes[i].voiceover.text` — record or generate that with a proper TTS
  voice).
- Drop background music at `audio_assets/bgm_scene_N.mp3`.

`audio.build_audio_track()` automatically mixes in any files it finds at
the correct offsets and volumes, and leaves silence where none exist. The
synthesized sound effects always play regardless.

## Known simplifications

- The character rig uses straight capsule limbs (line + round caps)
  rather than shaded sprite art — chosen because it's fast to render in
  pure Pillow, still cartoon-proportioned per spec, and keeps the whole
  pipeline dependency-free (no asset files to ship).
- `background_music.type` / `instruments` fields (Section 7) are
  documentation for a composer/TTS pass, not consumed by the renderer.
- A full-resolution render takes roughly 2 minutes on a single core
  (~20ms/frame for the drawing pass, plus x264 encoding).
