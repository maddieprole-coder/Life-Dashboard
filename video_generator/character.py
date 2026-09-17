"""Procedural rig for the 'main_cleaner' character (spec Section 4).

The character brief calls for "simple geometric proportions... simplified,
not anatomically detailed" cartoon shapes. This module renders that rig as
capsule-shaped limbs (a line plus round caps) pivoting from hip/shoulder
joints, using the exact dimensions and colours given in
spec/character.json / the cleaner character spec.
"""
import math
from PIL import Image, ImageDraw

from easing import hex_to_rgb

# Dimensions straight from spec Section 4 character.json
HEAD_RADIUS = 40
TORSO_WIDTH = 80
TORSO_HEIGHT = 120
ARM_LENGTH = 100
ARM_WIDTH = 20
LEG_LENGTH = 120
LEG_WIDTH = 24
SHOE_HEIGHT = 18
SHOE_WIDTH = 34

# Palette matched to the reference mascot: ponytail, white tee under blue
# denim overalls, yellow rubber gloves, yellow sneakers -- no hard hat/vest.
SKIN = hex_to_rgb("#F4C7A1")
HAIR = hex_to_rgb("#6B4226")
HAIR_TIE = hex_to_rgb("#E85D75")
SHIRT = hex_to_rgb("#FFFFFF")
OVERALLS = hex_to_rgb("#3E7FDB")
OVERALLS_DARK = hex_to_rgb("#2F63B0")
OVERALLS_BUTTON = hex_to_rgb("#FFD700")
TROUSERS = hex_to_rgb("#3E7FDB")
SHOE_COLOR = hex_to_rgb("#FFD700")
SHOE_SOLE = hex_to_rgb("#FFFFFF")
GLOVE = hex_to_rgb("#FFD700")
BLUSH = (255, 182, 193)
EYE_WHITE = (255, 255, 255)
EYE_PUPIL = (0, 0, 0)
MOUTH = hex_to_rgb("#8B4A3D")


def _pt(origin, angle_deg, length):
    """Point `length` away from origin, angle measured from straight-down (0deg)."""
    rad = math.radians(angle_deg)
    return (origin[0] + length * math.sin(rad), origin[1] + length * math.cos(rad))


def _capsule(draw, p0, p1, width, fill):
    draw.line([p0, p1], fill=fill, width=int(width))
    r = width / 2
    draw.ellipse([p0[0] - r, p0[1] - r, p0[0] + r, p0[1] + r], fill=fill)
    draw.ellipse([p1[0] - r, p1[1] - r, p1[0] + r, p1[1] + r], fill=fill)


def _arm_geometry(pose, side):
    """Shoulder origin, swing angle and hand point for one arm (shared by
    the renderer and by prop placement, e.g. the broom in render.py)."""
    scale = pose.get("scale", 1.0)
    facing = pose.get("facing", 1)
    hip = (pose["x"], pose["y"])
    torso_len = TORSO_HEIGHT * scale
    is_left = side == "left"
    shoulder_off = (-32 * scale * facing if is_left else 32 * scale * facing, -torso_len * 0.82)
    origin = (hip[0] + shoulder_off[0], hip[1] + shoulder_off[1])
    is_active_arm = not is_left
    angle = pose["left_arm_rotation" if is_left else "right_arm_rotation"] * facing
    if pose.get("hand_on_chin") and is_active_arm:
        angle = -150 * facing
    if pose.get("thumbs_up") and is_active_arm:
        angle = -170 * facing
    hand = _pt(origin, angle, ARM_LENGTH * scale)
    return origin, angle, hand


def hand_point(pose, side="left"):
    """Public helper: where a prop should attach to that hand."""
    return _arm_geometry(pose, side)[2]


def default_pose(**overrides):
    pose = dict(
        x=960, y=560,
        torso_rotation=0,
        left_leg_rotation=-8, right_leg_rotation=8,
        left_arm_rotation=6, right_arm_rotation=-6,
        head_tilt=0,
        expression="smile",
        hand_on_chin=False,
        thumbs_up=False,
        glow_color=None, glow_intensity=0.0,
        leg_glow_color=None, leg_glow_intensity=0.0,
        crouch=0.0,           # 0..1, shortens the effective leg length (knees bending)
        scale=1.0,
        facing=1,             # 1 = facing camera/right, -1 = mirrored
    )
    pose.update(overrides)
    return pose


def draw_character(canvas: Image.Image, pose: dict):
    draw = ImageDraw.Draw(canvas, "RGBA")
    scale = pose.get("scale", 1.0)
    facing = pose.get("facing", 1)
    hip = (pose["x"], pose["y"])

    leg_len = LEG_LENGTH * scale * (1 - 0.35 * pose.get("crouch", 0.0))
    leg_w = LEG_WIDTH * scale

    # --- glow halo (bend correct/wrong, leg highlight during lift) ---
    if pose.get("glow_color") and pose.get("glow_intensity", 0) > 0:
        glow = hex_to_rgb(pose["glow_color"])
        alpha = int(90 * pose["glow_intensity"])
        r = 170 * scale
        draw.ellipse([hip[0] - r, hip[1] - r * 1.3, hip[0] + r, hip[1] + r * 1.1],
                     fill=(*glow, alpha))

    # --- legs (denim) + sneakers ---
    for side, rot in (("left", pose["left_leg_rotation"] * facing),
                       ("right", pose["right_leg_rotation"] * facing)):
        hip_off = (-18 * scale * facing if side == "left" else 18 * scale * facing, 0)
        origin = (hip[0] + hip_off[0], hip[1] + hip_off[1])
        knee = _pt(origin, rot, leg_len)
        _capsule(draw, origin, knee, leg_w, TROUSERS)
        # ankle cuff
        cuff = _pt(origin, rot, leg_len * 0.9)
        _capsule(draw, cuff, knee, leg_w * 1.08, OVERALLS_DARK)
        bx, by = knee
        bw, bh = SHOE_WIDTH * scale, SHOE_HEIGHT * scale
        draw.ellipse([bx - bw / 2, by - bh / 3, bx + bw / 2, by + bh], fill=SHOE_COLOR)
        draw.ellipse([bx - bw / 2, by + bh * 0.45, bx + bw / 2, by + bh], fill=SHOE_SOLE)

    if pose.get("leg_glow_color") and pose.get("leg_glow_intensity", 0) > 0:
        glow = hex_to_rgb(pose["leg_glow_color"])
        alpha = int(120 * pose["leg_glow_intensity"])
        r = 60 * scale
        draw.ellipse([hip[0] - r, hip[1], hip[0] + r, hip[1] + leg_len + 20 * scale],
                     outline=(*glow, alpha), width=6)

    # --- torso: white tee, blue denim overalls bib + straps on top ---
    torso_len = TORSO_HEIGHT * scale
    neck = _pt(hip, pose["torso_rotation"] * facing, -torso_len)
    _capsule(draw, hip, neck, TORSO_WIDTH * scale, SHIRT)

    bib_top = _pt(hip, pose["torso_rotation"] * facing, -torso_len * 0.62)
    _capsule(draw, hip, bib_top, TORSO_WIDTH * scale * 0.9, OVERALLS)

    dx, dy = bib_top[0] - hip[0], bib_top[1] - hip[1]
    perp = (-dy, dx)
    plen = math.hypot(*perp) or 1
    perp = (perp[0] / plen, perp[1] / plen)

    # front pocket
    pocket_cx = hip[0] + dx * 0.55
    pocket_cy = hip[1] + dy * 0.55
    pw, ph = TORSO_WIDTH * scale * 0.28, TORSO_WIDTH * scale * 0.22
    draw.rounded_rectangle([pocket_cx - pw / 2, pocket_cy - ph / 2,
                             pocket_cx + pw / 2, pocket_cy + ph / 2],
                            radius=3 * scale, outline=OVERALLS_DARK, width=max(2, int(3 * scale)))

    # shoulder straps + buttons, from the bib top to each shoulder
    for sign in (-1, 1):
        span = TORSO_WIDTH * scale * 0.28 * sign
        strap_bottom = (bib_top[0] + perp[0] * span, bib_top[1] + perp[1] * span)
        strap_top = (neck[0] + sign * 22 * scale, neck[1] + 6 * scale)
        draw.line([strap_bottom, strap_top], fill=OVERALLS, width=max(3, int(10 * scale)))
        br = 4 * scale
        draw.ellipse([strap_bottom[0] - br, strap_bottom[1] - br,
                      strap_bottom[0] + br, strap_bottom[1] + br], fill=OVERALLS_BUTTON)

    # --- arms ---
    for side in ("left", "right"):
        is_active_arm = (side == "right")
        origin, angle, hand = _arm_geometry(pose, side)
        _capsule(draw, origin, hand, ARM_WIDTH * scale, SKIN)
        r = ARM_WIDTH * scale * 0.6
        draw.ellipse([hand[0] - r, hand[1] - r, hand[0] + r, hand[1] + r], fill=GLOVE)
        if pose.get("thumbs_up") and is_active_arm:
            tip = _pt(hand, angle - 60 * facing, 26 * scale)
            _capsule(draw, hand, tip, 8 * scale, GLOVE)

    # --- head ---
    hr = HEAD_RADIUS * scale
    head_c = _pt(neck, pose["torso_rotation"] * facing + pose.get("head_tilt", 0) * facing, -hr * 0.9)
    hx, hy = head_c

    # hair: a back halo (peeks above/behind the face), short front bangs, and
    # a single ponytail swept to one side and hanging past the shoulder.
    draw.ellipse([hx - hr * 1.1, hy - hr * 1.1, hx + hr * 1.1, hy + hr * 0.55], fill=HAIR)

    # opposite side from the (usually active) right arm, so waves/gestures
    # don't swing straight through the hair
    ponytail_side = -facing
    tie = (hx + ponytail_side * hr * 0.98, hy - hr * 0.1)
    tail_end = (hx + ponytail_side * hr * 1.55, hy + hr * 1.75)
    tail_mid = (hx + ponytail_side * hr * 1.75, hy + hr * 0.75)
    draw.line([tie, tail_mid, tail_end], fill=HAIR, width=int(hr * 0.42), joint="curve")
    r_end = hr * 0.14
    draw.ellipse([tail_end[0] - r_end, tail_end[1] - r_end, tail_end[0] + r_end, tail_end[1] + r_end],
                 fill=HAIR)

    # face
    draw.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=SKIN)

    # short front bangs
    draw.pieslice([hx - hr * 0.95, hy - hr * 1.05, hx + hr * 0.95, hy - hr * 0.15],
                  start=180, end=360, fill=HAIR)

    # hair tie band at the base of the ponytail
    tie_r = hr * 0.16
    draw.ellipse([tie[0] - tie_r, tie[1] - tie_r, tie[0] + tie_r, tie[1] + tie_r], fill=HAIR_TIE)

    # blush
    for sign in (-1, 1):
        bx = hx + sign * hr * 0.55
        by = hy + hr * 0.15
        br = hr * 0.18
        draw.ellipse([bx - br, by - br, bx + br, by + br], fill=(*BLUSH, 150))

    # eyes
    expression = pose.get("expression", "smile")
    eye_dy = hr * 0.9 if expression == "thoughtful" else hr * 1.0
    for sign in (-1, 1):
        ex = hx + sign * hr * 0.38
        ey = hy - hr * 0.05
        er = hr * 0.22
        draw.ellipse([ex - er, ey - er, ex + er, ey + er], fill=EYE_WHITE, outline=(0, 0, 0, 60))
        pr = er * 0.45
        px = ex + sign * er * 0.15
        py = ey + (er * 0.1 if expression != "focused" else 0)
        draw.ellipse([px - pr, py - pr, px + pr, py + pr], fill=EYE_PUPIL)
        gr = pr * 0.35
        draw.ellipse([px - gr, py - er * 0.35, px + gr, py - er * 0.15], fill=EYE_WHITE)

    # mouth
    mouth_curve = {
        "smile": 10, "proud_smile": 14, "thoughtful": 3, "determined": 2,
        "focused": 4, "satisfied": 12, "careful": 4, "thumbs_up": 14,
    }.get(expression, 8)
    mw = hr * 0.6
    my = hy + hr * 0.45
    draw.arc([hx - mw, my - mouth_curve, hx + mw, my + mouth_curve], start=20, end=160,
              fill=MOUTH, width=max(2, int(3 * scale)))

    return canvas
