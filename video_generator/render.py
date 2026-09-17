"""Frame-by-frame interpreter for spec/scenes.json.

Given a global frame number (0..total_frames-1) this produces a single
1920x1080 RGB frame (as a numpy array) by finding the active scene and
drawing every element that is "live" at that frame, using the exact
positions/colours/timings from the spec JSON.
"""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw

import animations
import character
import icons
import objects
import text_utils
from easing import clamp01, ease_in, ease_out, hex_to_rgb, lerp, progress as prog

SPEC_DIR = os.path.join(os.path.dirname(__file__), "spec")

with open(os.path.join(SPEC_DIR, "metadata.json")) as f:
    METADATA = json.load(f)["video_project"]
with open(os.path.join(SPEC_DIR, "colors.json")) as f:
    COLORS = json.load(f)["colors"]
with open(os.path.join(SPEC_DIR, "scenes.json")) as f:
    SCENES = json.load(f)

WIDTH = METADATA["resolution"]["width"]
HEIGHT = METADATA["resolution"]["height"]
FPS = METADATA["fps"]
TOTAL_FRAMES = METADATA["total_frames"]


def scene_for_frame(frame):
    for scene in SCENES:
        if scene["start_frame"] <= frame < scene["end_frame"]:
            return scene
    return SCENES[-1]


def _elem_window(element, scene):
    start = element.get("start_frame", scene["start_frame"])
    duration = element.get("duration_frames", scene["end_frame"] - start)
    return start, duration


def draw_background(canvas, scene):
    draw = ImageDraw.Draw(canvas)
    top = hex_to_rgb(scene.get("background_color", "#FFFFFF"))
    if scene.get("background_gradient") and scene.get("gradient_bottom_color"):
        bottom = hex_to_rgb(scene["gradient_bottom_color"])
        for y in range(HEIGHT):
            t = y / HEIGHT
            row = tuple(int(lerp(top[c], bottom[c], t)) for c in range(3))
            draw.line([(0, y), (WIDTH, y)], fill=row)
    else:
        draw.rectangle([0, 0, WIDTH, HEIGHT], fill=top)


# ---------------------------------------------------------------- elements

# The reference mascot always carries a broom in its idle hand. We keep that
# only for scenes where both hands aren't already busy with the bucket/lift
# mechanic, so the broom doesn't collide with the lifting demonstration.
BROOM_ANIMATIONS = {"wave_friendly", "assess_load", "position_feet"}


def draw_character_element(canvas, element, scene, frame):
    start, duration = _elem_window(element, scene)
    local = frame - start
    anim_name = element.get("animation")
    pose = animations.get_pose(anim_name, local, duration, element)
    character.draw_character(canvas, pose)
    if element.get("bucket_held"):
        rel = element.get("bucket_position_relative", {"x": 0, "y": -60})
        objects.draw_mop_bucket(canvas, pose["x"] + rel["x"], pose["y"] + rel["y"], scale=0.7)
    if anim_name in BROOM_ANIMATIONS:
        scale = pose.get("scale", 1.0)
        hx, hy = character.hand_point(pose, "left")
        objects.draw_broom(canvas, hx, hy, angle=-15 * pose.get("facing", 1), scale=scale)


def draw_object_element(canvas, element, scene, frame):
    if element.get("name") != "mop_bucket":
        return
    start, duration = _elem_window(element, scene)
    local = max(0, frame - start)
    pos = element["position"]
    anim = element.get("animation")

    if anim == "rotate_slow":
        rotation = (local * (360 / (8 * FPS))) % 360
        objects.draw_mop_bucket(canvas, pos["x"], pos["y"], rotation=rotation)
    elif anim in ("lift_smooth", "lower_gently"):
        end = element.get("end_position", pos)
        t = prog(frame, start, duration)
        e = ease_out(t) if anim == "lift_smooth" else ease_in(t)
        x = lerp(pos["x"], end["x"], e)
        y = lerp(pos["y"], end["y"], e)
        objects.draw_mop_bucket(canvas, x, y)
        if anim == "lift_smooth" and element.get("arrow_indicators") and t < 1:
            draw = ImageDraw.Draw(canvas, "RGBA")
            c = hex_to_rgb(element.get("arrow_color", "#00AA00"))
            ax = x + 70
            draw.line([(ax, y + 20), (ax, y - 20)], fill=(*c, 220), width=6)
            draw.polygon([(ax - 12, y - 14), (ax + 12, y - 14), (ax, y - 34)], fill=(*c, 220))
    else:
        objects.draw_mop_bucket(canvas, pos["x"], pos["y"])


def draw_icon_element(canvas, element, scene, frame):
    start, duration = _elem_window(element, scene)
    t = prog(frame, start, duration)
    pos = element.get("position", {"x": WIDTH // 2, "y": HEIGHT // 2})
    size = element.get("size", 70)
    anim = element.get("animation")

    if anim == "fade_in_pulse":
        alpha = int(255 * ease_out(min(1, t * 2)))
        pulse = 1 + 0.08 * math.sin(frame / 6)
        icons.draw_icon(canvas, element["name"], pos["x"], pos["y"], size * pulse,
                         color=element.get("color"), alpha=alpha)
    elif anim in ("appear_with_scale", "scale_in"):
        s = ease_out(t)
        icons.draw_icon(canvas, element["name"], pos["x"], pos["y"], size * s,
                         color=element.get("color"), alpha=int(255 * clamp01(t * 3)))
    else:
        icons.draw_icon(canvas, element["name"], pos["x"], pos["y"], size,
                         color=element.get("color"))


def draw_floating_icons(canvas, element, scene, frame):
    start = element.get("start_frame", scene["start_frame"])
    duration = element["duration_frames"]
    names = element["icons"]
    n = len(names)
    cx, cy, radius = WIDTH // 2, HEIGHT // 2 - 40, 260
    for i, name in enumerate(names):
        stagger = i * (duration / n) * 0.4
        t = prog(frame, start + stagger, duration * 0.6)
        angle = (2 * math.pi * i / n) - math.pi / 2
        r = radius * ease_out(t)
        x = cx + math.cos(angle) * r
        y = cy + math.sin(angle) * r * 0.7
        icons.draw_icon(canvas, name, x, y, 56, alpha=int(255 * t))


def draw_graphic_element(canvas, element, scene, frame):
    start, duration = _elem_window(element, scene)
    t = prog(frame, start, duration)
    name = element["name"]
    pos = element.get("position", {"x": WIDTH // 2, "y": HEIGHT - 250})
    color = hex_to_rgb(element.get("color", "#00AA00"))
    alpha = int(255 * element.get("opacity", 1.0) * ease_out(t))
    draw = ImageDraw.Draw(canvas, "RGBA")

    if name == "footprints_outline":
        for sign in (-1, 1):
            fx = pos["x"] + sign * 40
            draw.ellipse([fx - 18, pos["y"] - 30, fx + 18, pos["y"] + 30],
                         outline=(*color, alpha), width=4)
    elif name == "distance_markers":
        y = pos["y"] + 60
        draw.line([(pos["x"] - 40, y), (pos["x"] + 40, y)], fill=(*color, alpha), width=3)
        for sx in (pos["x"] - 40, pos["x"] + 40):
            draw.line([(sx, y - 10), (sx, y + 10)], fill=(*color, alpha), width=3)
        label = element.get("label_text", "")
        font = text_utils.get_font("Arial", 28)
        draw.text((pos["x"] - 60, y + 14), label, font=font, fill=(*color, alpha))
    elif name == "walking_path":
        y = HEIGHT - 260
        for x in range(400, 1521, 40):
            draw.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(*color, alpha))
    elif name == "safe_zone_highlight":
        draw.rectangle([300, HEIGHT - 320, 1620, HEIGHT - 180], fill=(*color, int(alpha * 0.5)))


def draw_split_screen(canvas, element, scene, frame):
    start, duration = _elem_window(element, scene)
    local = frame - start
    left, right = element["left_side"], element["right_side"]
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.line([(WIDTH // 2, 220), (WIDTH // 2, HEIGHT - 60)], fill=(200, 200, 200, 160), width=3)

    for side, style in ((left, "correct"), (right, "wrong")):
        pos = side["position"]
        pose = animations.pose_bend(max(0, local), duration, pos["x"], pos["y"], style=style)
        character.draw_character(canvas, pose)
        font = text_utils.get_font("Arial Bold", 40)
        color = hex_to_rgb("#00AA00" if style == "correct" else "#FF4444")
        bbox = draw.textbbox((0, 0), side["label"], font=font)
        tw = bbox[2] - bbox[0]
        draw.text((pos["x"] - tw / 2, 260), side["label"], font=font, fill=color)


def draw_character_overlay(canvas, element, scene, frame):
    start, duration = _elem_window(element, scene)
    t = prog(frame, start, duration)
    pos = element["position"]
    color = hex_to_rgb(element["color"])
    draw = ImageDraw.Draw(canvas, "RGBA")
    top = (pos["x"], pos["y"] - 150)
    bottom = (pos["x"], pos["y"])
    end = (lerp(top[0], bottom[0], t), lerp(top[1], bottom[1], t))
    if "curved" in element.get("animation", ""):
        mid = ((top[0] + end[0]) / 2 + 25, (top[1] + end[1]) / 2)
        draw.line([top, mid, end], fill=(*color, 230), width=element.get("thickness", 4), joint="curve")
    else:
        draw.line([top, end], fill=(*color, 230), width=element.get("thickness", 4))


def draw_visual_effect(canvas, element, scene, frame):
    start, duration = _elem_window(element, scene)
    t = prog(frame, start, duration)
    name = element["name"]
    draw = ImageDraw.Draw(canvas, "RGBA")

    if name == "success_sparkles":
        pos = element["position"]
        color = hex_to_rgb(element.get("color", "#FFD700"))
        n = element.get("particle_count", 12)
        for i in range(n):
            angle = 2 * math.pi * i / n
            r = 90 * ease_out(t)
            x = pos["x"] + math.cos(angle) * r
            y = pos["y"] + math.sin(angle) * r
            alpha = int(255 * (1 - t))
            draw.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(*color, alpha))
    elif name == "icon_circle_arrangement":
        pos = element["position"]
        names = element["icons"]
        radius = element.get("radius", 300) * ease_out(t)
        n = len(names)
        for i, icon_name in enumerate(names):
            angle = 2 * math.pi * i / n - math.pi / 2
            x = pos["x"] + math.cos(angle) * radius
            y = pos["y"] + math.sin(angle) * radius * 0.7
            icons.draw_icon(canvas, icon_name, x, y, 50, alpha=int(255 * t))
    elif name == "equipment_glow":
        color = hex_to_rgb(element.get("glow_color", "#FFD700"))
        intensity = element.get("glow_intensity", 0.5)
        alpha = int(90 * intensity * math.sin(t * math.pi))
        draw.ellipse([WIDTH / 2 - 320, HEIGHT / 2 - 220, WIDTH / 2 + 320, HEIGHT / 2 + 220],
                     fill=(*color, max(0, alpha)))


def draw_animation_event(canvas, element, scene, frame):
    start = element.get("frame", element.get("start_frame", scene["start_frame"]))
    duration = element.get("duration_frames", 60)
    t = prog(frame, start, duration)
    if t <= 0:
        return
    name = element["name"]

    if name == "completion_checkmark" or name == "show_checkmark_over_bucket":
        icons.draw_icon(canvas, "checkmark", 960, 620, element.get("size", 120) * ease_out(t),
                         color=element.get("color", "#00AA00"), alpha=int(255 * clamp01(t * 3)))
    elif name in ("thumbs_up_gesture", "character_thumbs_up"):
        pose = character.default_pose(x=960, y=500, thumbs_up=True, expression="proud_smile")
        character.draw_character(canvas, pose)
    elif name in ("show_wrong_twist", "show_wrong_reach"):
        color = hex_to_rgb(element.get("wrong_color") or element.get("correction_color", "#FF4444"))
        draw = ImageDraw.Draw(canvas, "RGBA")
        flash = int(120 * math.sin(min(1, t) * math.pi))
        draw.rectangle([0, 0, WIDTH, HEIGHT], fill=(*color, max(0, flash) // 6))


def draw_fade(canvas, element, scene, frame):
    """fade_in / fade_out are applied globally after the scene is composed."""
    return None


ELEMENT_HANDLERS = {
    "character": draw_character_element,
    "object": draw_object_element,
    "icon": draw_icon_element,
    "floating_icons": draw_floating_icons,
    "graphic_element": draw_graphic_element,
    "split_screen": draw_split_screen,
    "character_overlay": draw_character_overlay,
    "visual_effect": draw_visual_effect,
    "animation_event": draw_animation_event,
    "text_title": lambda c, e, s, f: text_utils.draw_text_element(
        c, e, f - e.get("start_frame", s["start_frame"]), e.get("duration_frames", 100)),
    "text_subtitle": lambda c, e, s, f: text_utils.draw_text_element(
        c, e, f - e.get("start_frame", s["start_frame"]), e.get("duration_frames", 100)),
    "text_callout": lambda c, e, s, f: text_utils.draw_text_element(
        c, e, f - e.get("start_frame", s["start_frame"]), e.get("duration_frames", 100)),
    "fade_in": draw_fade,
    "fade_out": draw_fade,
}


def _scene_fade_multiplier(scene, frame):
    alpha = 1.0
    for element in scene["elements"]:
        if element["type"] == "fade_in":
            start = element.get("start_frame", scene["start_frame"])
            alpha = min(alpha, prog(frame, start, element["duration_frames"]))
        elif element["type"] == "fade_out":
            start = element.get("start_frame", scene["start_frame"])
            alpha = min(alpha, 1 - prog(frame, start, element["duration_frames"]))
    return alpha


def render_frame(frame: int) -> np.ndarray:
    scene = scene_for_frame(frame)
    canvas = Image.new("RGB", (WIDTH, HEIGHT), hex_to_rgb(scene.get("background_color", "#FFFFFF")))
    draw_background(canvas, scene)
    canvas = canvas.convert("RGBA")

    for element in scene["elements"]:
        start = element.get("start_frame", scene["start_frame"])
        duration = element.get("duration_frames", scene["end_frame"] - start)
        end_frame = element.get("frame")
        if end_frame is not None:
            live = frame >= end_frame
        else:
            live = start <= frame
        if not live:
            continue
        handler = ELEMENT_HANDLERS.get(element["type"])
        if handler:
            # Draw onto a transparent layer and alpha-composite it onto the
            # canvas: raw ImageDraw fills on a shared RGBA image overwrite
            # pixels (including their alpha) rather than blending, which
            # would make every translucent effect either invisible or, for
            # full-frame overlays like the "wrong move" flash, opaque.
            layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
            handler(layer, element, scene, frame)
            canvas = Image.alpha_composite(canvas, layer)

    fade = _scene_fade_multiplier(scene, frame)
    if fade < 1.0:
        white = Image.new("RGBA", canvas.size, (255, 255, 255, 255))
        canvas = Image.blend(white, canvas, fade)

    return np.array(canvas.convert("RGB"))
