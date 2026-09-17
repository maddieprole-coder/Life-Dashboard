"""Text drawing + the spec's text animations (fade_in, slide_up, slide_in*)."""
from PIL import ImageDraw, ImageFont
from easing import ease_out, lerp, progress as prog, hex_to_rgb

FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT_REGULAR = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

_font_cache = {}


def get_font(name, size):
    path = FONT_BOLD if "Bold" in name else FONT_REGULAR
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


def draw_text_element(canvas, element, local_frame, duration):
    """Renders text_title / text_subtitle / text_callout with their animation."""
    draw = ImageDraw.Draw(canvas, "RGBA")
    text = element["text"]
    pos = element["position"]
    font = get_font(element.get("font", "Arial"), element.get("font_size", 40))
    color = hex_to_rgb(element.get("color", "#000000"))
    anim = element.get("animation", "fade_in")
    t = prog(local_frame, 0, duration)
    e = ease_out(t)

    x, y = pos["x"], pos["y"]
    opacity = 255

    if anim == "fade_in":
        opacity = int(255 * e)
    elif anim in ("slide_up",):
        y = lerp(y + 60, y, e)
        opacity = int(255 * e)
    elif anim in ("slide_in_from_bottom",):
        y = lerp(y + 80, y, e)
        opacity = int(255 * e)
    elif anim == "slide_in":
        x = lerp(x - 200, x, e)
        opacity = int(255 * e)

    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    if element.get("background_box"):
        pad_x, pad_y = 24, 14
        box = [x - tw / 2 - pad_x, y - th / 2 - pad_y, x + tw / 2 + pad_x, y + th / 2 + pad_y]
        radius = element.get("background_radius", 12)
        draw.rounded_rectangle(box, radius=radius, fill=(255, 255, 255, int(200 * (opacity / 255))))

    draw.text((x - tw / 2, y - th / 2 - bbox[1]), text, font=font, fill=(*color, opacity))
