"""Props (spec Section 5): the mop_bucket, restyled as a wheeled cleaning
cart to match the reference character, plus a broom the character carries."""
import math
from PIL import ImageDraw
from easing import hex_to_rgb

BODY = hex_to_rgb("#3E7FDB")
BORDER = hex_to_rgb("#2F63B0")
CONTENTS = hex_to_rgb("#87CEEB")
TRIM = hex_to_rgb("#FFD700")
WHEEL = hex_to_rgb("#333333")
BOTTLE_COLORS = (hex_to_rgb("#4CAF50"), hex_to_rgb("#FF8800"))

BROOM_HANDLE = hex_to_rgb("#C9A46A")
BROOM_BAND = hex_to_rgb("#FFD700")
BROOM_BRISTLES = hex_to_rgb("#3E7FDB")

WIDTH = 60
HEIGHT = 50


def draw_mop_bucket(canvas, x, y, rotation=0.0, fill_level=0.85, scale=1.0):
    draw = ImageDraw.Draw(canvas, "RGBA")
    w, h = WIDTH * scale, HEIGHT * scale
    # "rotate_slow" (Section 5) is a lazy-susan style spin; approximate with
    # a horizontal squash so the spin reads even in a static raster frame.
    squash = abs(math.cos(math.radians(rotation)))
    hw = w / 2 * max(0.35, squash)

    box = [x - hw, y - h / 2, x + hw, y + h / 2]
    draw.rounded_rectangle(box, radius=6 * scale, fill=BODY, outline=BORDER, width=3)

    fill_top = box[1] + h * (1 - fill_level)
    draw.rounded_rectangle([box[0] + 4, fill_top, box[2] - 4, box[3] - 4],
                            radius=4 * scale, fill=CONTENTS)

    # trim band + wheels give the "wheeled cleaning cart" read from the reference art
    draw.rectangle([box[0], box[3] - 5 * scale, box[2], box[3]], fill=TRIM)
    for wx in (box[0] + hw * 0.4, box[2] - hw * 0.4):
        wr = 6 * scale
        draw.ellipse([wx - wr, box[3] - wr * 0.6, wx + wr, box[3] + wr * 1.2], fill=WHEEL)

    for i, bc in enumerate(BOTTLE_COLORS):
        bx = box[0] + hw * (0.5 + i * 0.7)
        draw.rectangle([bx - 4 * scale, fill_top - 16 * scale, bx + 4 * scale, fill_top + 2 * scale],
                        fill=bc)

    handle_y = box[1]
    draw.arc([x - hw * 0.9, handle_y - 22 * scale, x + hw * 0.9, handle_y + 14 * scale],
              start=180, end=360, fill=BORDER, width=int(4 * scale))
    return canvas


def draw_broom(canvas, x, y, angle=12.0, length=170.0, scale=1.0):
    """A broom leaning against/held beside the character, handle top at (x, y)."""
    draw = ImageDraw.Draw(canvas, "RGBA")
    rad = math.radians(angle)
    length *= scale
    end = (x + length * math.sin(rad), y + length * math.cos(rad))
    draw.line([(x, y), end], fill=BROOM_HANDLE, width=max(3, int(6 * scale)))

    bristle_len = 46 * scale
    tip = (end[0] + bristle_len * math.sin(rad), end[1] + bristle_len * math.cos(rad))
    perp = (math.cos(rad), -math.sin(rad))
    spread = 26 * scale
    left = (tip[0] + perp[0] * spread, tip[1] + perp[1] * spread)
    right = (tip[0] - perp[0] * spread, tip[1] - perp[1] * spread)
    draw.polygon([end, left, right], fill=BROOM_BRISTLES)
    draw.line([left, right], fill=BROOM_BRISTLES, width=max(2, int(3 * scale)))

    band_r = 7 * scale
    draw.ellipse([end[0] - band_r, end[1] - band_r, end[0] + band_r, end[1] + band_r],
                 fill=BROOM_BAND)
    return canvas
