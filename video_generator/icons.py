"""Small geometric icon glyphs used for floating_icons / icon elements."""
from PIL import ImageDraw
from easing import hex_to_rgb

WHITE = (255, 255, 255)
YELLOW = hex_to_rgb("#FFD700")
BLUE = hex_to_rgb("#0088FF")
RED = hex_to_rgb("#FF4444")
GREEN = hex_to_rgb("#00AA00")
GREY = hex_to_rgb("#2C2C2C")
TAN = hex_to_rgb("#D2B48C")


def draw_icon(canvas, name, x, y, size=60, color=None, alpha=255):
    draw = ImageDraw.Draw(canvas, "RGBA")
    r = size / 2
    box = [x - r, y - r, x + r, y + r]

    def rgba(c):
        return (*c, alpha)

    if name == "hard_hat":
        draw.pieslice([x - r, y - r * 0.8, x + r, y + r * 0.6], 180, 360, fill=rgba(WHITE))
        draw.rectangle([x - r, y + r * 0.1, x + r, y + r * 0.3], fill=rgba(WHITE))
    elif name == "safety_vest":
        draw.polygon([(x - r * 0.6, y - r), (x + r * 0.6, y - r),
                      (x + r * 0.8, y + r), (x - r * 0.8, y + r)], fill=rgba(YELLOW))
        draw.line([(x - r * 0.6, y - r), (x + r * 0.6, y + r)], fill=rgba(WHITE), width=3)
        draw.line([(x + r * 0.6, y - r), (x - r * 0.6, y + r)], fill=rgba(WHITE), width=3)
    elif name == "goggles":
        for sign in (-1, 1):
            cx = x + sign * r * 0.45
            draw.ellipse([cx - r * 0.4, y - r * 0.3, cx + r * 0.4, y + r * 0.3],
                         outline=rgba(GREY), width=3, fill=rgba(BLUE))
        draw.line([(x - r * 0.1, y), (x + r * 0.1, y)], fill=rgba(GREY), width=3)
    elif name == "gloves":
        draw.ellipse(box, fill=rgba(TAN))
        for i in range(4):
            fx = x - r * 0.5 + i * r * 0.33
            draw.line([(fx, y - r * 0.2), (fx, y - r)], fill=rgba(TAN), width=6)
    elif name == "boots":
        draw.rectangle([x - r * 0.4, y - r, x + r * 0.4, y + r * 0.3], fill=rgba(YELLOW))
        draw.ellipse([x - r * 0.5, y, x + r * 0.9, y + r * 0.6], fill=rgba(YELLOW))
        draw.rectangle([x - r * 0.5, y + r * 0.35, x + r * 0.9, y + r * 0.6], fill=rgba(GREY))
    elif name == "warning_triangle" or name == "warning_caution":
        draw.polygon([(x, y - r), (x + r, y + r), (x - r, y + r)],
                     outline=rgba(RED), width=4, fill=rgba((255, 221, 51)))
        draw.text((x - 4, y - 2), "!", fill=rgba(GREY))
    elif name == "first_aid_kit":
        draw.rounded_rectangle(box, radius=r * 0.2, fill=rgba(WHITE), outline=rgba(RED), width=3)
        draw.line([(x - r * 0.4, y), (x + r * 0.4, y)], fill=rgba(RED), width=6)
        draw.line([(x, y - r * 0.4), (x, y + r * 0.4)], fill=rgba(RED), width=6)
    elif name in ("checkmark_green", "checkmark_correct", "checkmark_arrival", "checkmark"):
        c = hex_to_rgb(color) if color else GREEN
        draw.line([(x - r * 0.6, y), (x - r * 0.1, y + r * 0.5)], fill=rgba(c), width=8)
        draw.line([(x - r * 0.1, y + r * 0.5), (x + r * 0.7, y - r * 0.5)], fill=rgba(c), width=8)
    elif name in ("x_mark_wrong", "x_mark"):
        c = hex_to_rgb(color) if color else RED
        draw.line([(x - r * 0.6, y - r * 0.6), (x + r * 0.6, y + r * 0.6)], fill=rgba(c), width=8)
        draw.line([(x - r * 0.6, y + r * 0.6), (x + r * 0.6, y - r * 0.6)], fill=rgba(c), width=8)
    elif name == "weight_symbol":
        c = hex_to_rgb(color) if color else RED
        draw.rounded_rectangle([x - r * 0.8, y - r * 0.5, x + r * 0.8, y + r * 0.6],
                                radius=6, fill=rgba(c))
        draw.arc([x - r * 0.35, y - r * 0.9, x + r * 0.35, y - r * 0.25], 180, 360,
                  fill=rgba(c), width=5)
    else:
        draw.ellipse(box, outline=rgba(GREY), width=3)
    return canvas
