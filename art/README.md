# Hatsune Miku — semi-realistic portrait

A hand-built MikuPaint project: **2,600+ editable vector shapes** (polygons, ovals,
lines and text) on a 1200×1600 canvas.

| File | What it is |
|---|---|
| `hatsune_miku.mipaint` | The editable MikuPaint project — open it with **OPEN** in MikuPaint |
| `hatsune_miku.png` | An anti-aliased preview rendered from the exact same shapes |
| `draw_miku.py` | The generator that writes both files |

## Open it

```bash
python MikuPaint/main.py
```

Then **OPEN** → `art/hatsune_miku.mipaint`.

The portrait uses the polygon and round-line support that MikuPaint now restores
when opening and saving projects, so every lock of hair stays editable.

## Regenerate the files

The preview renderer uses Pillow; the paint app itself remains dependency-free.

```bash
python -m pip install pillow
python art/draw_miku.py
```

The drawing is procedural, so tweaking colours, coordinates or a few of the
helper functions in `draw_miku.py` is an easy way to make the portrait your own.
