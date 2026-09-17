"""The mop_bucket prop (spec Section 5)."""
import math
from PIL import ImageDraw
from easing import hex_to_rgb

BODY = hex_to_rgb("#4ECDC4")
BORDER = (45, 154, 138)
CONTENTS = hex_to_rgb("#87CEEB")

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

    handle_y = box[1]
    draw.arc([x - hw * 0.9, handle_y - 22 * scale, x + hw * 0.9, handle_y + 14 * scale],
              start=180, end=360, fill=BORDER, width=int(4 * scale))
    return canvas
