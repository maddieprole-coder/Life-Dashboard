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
BOOT_HEIGHT = 22
BOOT_WIDTH = 34

SKIN = hex_to_rgb("#D4A574")
HAIR = hex_to_rgb("#4A2C1A")
VEST = hex_to_rgb("#FFD700")
VEST_STRIPE = hex_to_rgb("#FFFFFF")
SHIRT = hex_to_rgb("#87CEEB")
TROUSERS = hex_to_rgb("#2C3E50")
BOOT_COLOR = hex_to_rgb("#FFD700")
BOOT_SOLE = hex_to_rgb("#2C2C2C")
HARDHAT = hex_to_rgb("#FFFFFF")
HARDHAT_LOGO = hex_to_rgb("#333333")
GLOVE_TAN = hex_to_rgb("#D2B48C")
BLUSH = (255, 182, 193)
EYE_WHITE = (255, 255, 255)
EYE_IRIS = hex_to_rgb("#0088FF")
EYE_PUPIL = (0, 0, 0)
MOUTH = hex_to_rgb("#333333")


def _pt(origin, angle_deg, length):
    """Point `length` away from origin, angle measured from straight-down (0deg)."""
    rad = math.radians(angle_deg)
    return (origin[0] + length * math.sin(rad), origin[1] + length * math.cos(rad))


def _capsule(draw, p0, p1, width, fill):
    draw.line([p0, p1], fill=fill, width=int(width))
    r = width / 2
    draw.ellipse([p0[0] - r, p0[1] - r, p0[0] + r, p0[1] + r], fill=fill)
    draw.ellipse([p1[0] - r, p1[1] - r, p1[0] + r, p1[1] + r], fill=fill)


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
        gloves=False,
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

    # --- legs + boots ---
    for side, rot in (("left", pose["left_leg_rotation"] * facing),
                       ("right", pose["right_leg_rotation"] * facing)):
        hip_off = (-18 * scale * facing if side == "left" else 18 * scale * facing, 0)
        origin = (hip[0] + hip_off[0], hip[1] + hip_off[1])
        knee = _pt(origin, rot, leg_len)
        _capsule(draw, origin, knee, leg_w, TROUSERS)
        boot_angle_rad = math.radians(rot)
        bx, by = knee
        bw, bh = BOOT_WIDTH * scale, BOOT_HEIGHT * scale
        draw.ellipse([bx - bw / 2, by - bh / 3, bx + bw / 2, by + bh], fill=BOOT_COLOR)
        draw.rectangle([bx - bw / 2, by + bh * 0.55, bx + bw / 2, by + bh], fill=BOOT_SOLE)

    if pose.get("leg_glow_color") and pose.get("leg_glow_intensity", 0) > 0:
        glow = hex_to_rgb(pose["leg_glow_color"])
        alpha = int(120 * pose["leg_glow_intensity"])
        r = 60 * scale
        draw.ellipse([hip[0] - r, hip[1], hip[0] + r, hip[1] + leg_len + 20 * scale],
                     outline=(*glow, alpha), width=6)

    # --- torso capsule (bends at hip for "bend your knees not your back") ---
    torso_len = TORSO_HEIGHT * scale
    neck = _pt(hip, pose["torso_rotation"] * facing, -torso_len)
    _capsule(draw, hip, neck, TORSO_WIDTH * scale, SHIRT)

    # vest over shirt (slightly narrower capsule + X stripes)
    vest_top = _pt(hip, pose["torso_rotation"] * facing, -torso_len * 0.92)
    _capsule(draw, hip, vest_top, TORSO_WIDTH * scale * 0.86, VEST)
    dx, dy = vest_top[0] - hip[0], vest_top[1] - hip[1]
    for t in (0.15, 0.5, 0.85):
        cx_, cy_ = hip[0] + dx * t, hip[1] + dy * t
        span = TORSO_WIDTH * scale * 0.4
        perp = (-dy, dx)
        plen = math.hypot(*perp) or 1
        perp = (perp[0] / plen * span, perp[1] / plen * span)
        draw.line([(cx_ - perp[0], cy_ - perp[1]), (cx_ + perp[0], cy_ + perp[1])],
                   fill=VEST_STRIPE, width=max(2, int(4 * scale)))

    # --- arms ---
    for side, rot in (("left", pose["left_arm_rotation"] * facing),
                       ("right", pose["right_arm_rotation"] * facing)):
        shoulder_off = (-32 * scale * facing if side == "left" else 32 * scale * facing,
                        -torso_len * 0.82)
        origin = (hip[0] + shoulder_off[0], hip[1] + shoulder_off[1])
        is_active_arm = (side == "right")
        angle = rot
        if pose.get("hand_on_chin") and is_active_arm:
            angle = -150 * facing
        if pose.get("thumbs_up") and is_active_arm:
            angle = -170 * facing
        hand = _pt(origin, angle, ARM_LENGTH * scale)
        _capsule(draw, origin, hand, ARM_WIDTH * scale, SKIN)
        hand_color = GLOVE_TAN if pose.get("gloves") else SKIN
        r = ARM_WIDTH * scale * 0.55
        draw.ellipse([hand[0] - r, hand[1] - r, hand[0] + r, hand[1] + r], fill=hand_color)
        if pose.get("thumbs_up") and is_active_arm:
            tip = _pt(hand, angle - 60 * facing, 26 * scale)
            _capsule(draw, hand, tip, 8 * scale, hand_color)

    # --- head ---
    hr = HEAD_RADIUS * scale
    head_c = _pt(neck, pose["torso_rotation"] * facing + pose.get("head_tilt", 0) * facing, -hr * 0.9)
    hx, hy = head_c

    # hair: a back halo (peeks above/behind the face) plus two side panels that
    # hang to shoulder height beside the face -- never crossing under the chin,
    # so it reads as hair, not a beard.
    draw.ellipse([hx - hr * 1.12, hy - hr * 1.12, hx + hr * 1.12, hy + hr * 0.7], fill=HAIR)
    for sign in (-1, 1):
        panel_cx = hx + sign * hr * 0.95
        draw.rounded_rectangle(
            [panel_cx - hr * 0.28, hy - hr * 0.3, panel_cx + hr * 0.28, hy + hr * 1.7],
            radius=hr * 0.26, fill=HAIR)

    # face
    draw.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=SKIN)

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

    # hard hat
    hat_top = hy - hr * 0.55
    draw.pieslice([hx - hr * 1.05, hat_top - hr * 0.95, hx + hr * 1.05, hat_top + hr * 0.55],
                  start=180, end=360, fill=HARDHAT, outline=(200, 200, 200, 255))
    draw.rectangle([hx - hr * 1.1, hat_top + hr * 0.15, hx + hr * 1.1, hat_top + hr * 0.32],
                    fill=HARDHAT)
    lr = hr * 0.16
    draw.ellipse([hx - lr, hat_top - hr * 0.15 - lr, hx + lr, hat_top - hr * 0.15 + lr],
                 outline=HARDHAT_LOGO, width=2)

    return canvas
