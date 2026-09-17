"""Procedural rig for the 'main_cleaner' character, styled to match a
reference mascot image: chibi proportions (big head, short body), a
two-segment elbow/knee rig instead of single rigid rods, rounded
hand/foot shapes, and soft blurred highlights faking glossy 3D shading.
"""
import math
from PIL import Image, ImageDraw, ImageFilter

from easing import hex_to_rgb

# Mildly chibi: bigger head and chunkier hands/feet than the original rig,
# but close enough to its total height that the spec's absolute pixel
# positions (bucket/text placement relative to the character) still line up.
HEAD_RADIUS = 46
TORSO_WIDTH = 70
TORSO_HEIGHT = 100
UPPER_ARM_LEN = 46
FOREARM_LEN = 50
ARM_WIDTH = 20
HAND_R = 15
THIGH_LEN = 52
SHIN_LEN = 52
LEG_WIDTH = 25
SHOE_WIDTH = 40
SHOE_HEIGHT = 25

SKIN = hex_to_rgb("#F4C7A1")
SKIN_LIGHT = hex_to_rgb("#FFE3C7")
HAIR = hex_to_rgb("#6B4226")
HAIR_LIGHT = hex_to_rgb("#8A5A34")
HAIR_TIE = hex_to_rgb("#E85D75")
SHIRT = hex_to_rgb("#FFFFFF")
OVERALLS = hex_to_rgb("#3E7FDB")
OVERALLS_LIGHT = hex_to_rgb("#6CA0EC")
OVERALLS_DARK = hex_to_rgb("#2F63B0")
OVERALLS_BUTTON = hex_to_rgb("#FFD700")
SHOE_COLOR = hex_to_rgb("#FFD700")
SHOE_DARK = hex_to_rgb("#E8B800")
SHOE_SOLE = hex_to_rgb("#FFFFFF")
GLOVE = hex_to_rgb("#FFD700")
GLOVE_DARK = hex_to_rgb("#E8B800")
BLUSH = (255, 182, 193)
EYE_WHITE = (255, 255, 255)
EYE_IRIS = hex_to_rgb("#4A2E1A")
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


def _highlight(canvas, cx, cy, rx, ry, color, alpha=90, blur=7):
    """A soft blurred light patch, to fake glossy 3D shading on flat fills."""
    pad = blur * 2 + 4
    w, h = int(rx * 2 + pad * 2), int(ry * 2 + pad * 2)
    patch = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(patch).ellipse([pad, pad, pad + rx * 2, pad + ry * 2], fill=(*color, alpha))
    patch = patch.filter(ImageFilter.GaussianBlur(blur))
    canvas.paste(patch, (int(cx - w / 2), int(cy - h / 2)), patch)


def _arm_geometry(pose, side):
    """Shoulder/elbow/hand points for one arm -- shared by the renderer and
    by prop placement (e.g. the broom in render.py)."""
    scale = pose.get("scale", 1.0)
    facing = pose.get("facing", 1)
    hip = (pose["x"], pose["y"])
    torso_len = TORSO_HEIGHT * scale
    is_left = side == "left"
    shoulder_off = (-28 * scale * facing if is_left else 28 * scale * facing, -torso_len * 0.86)
    shoulder = (hip[0] + shoulder_off[0], hip[1] + shoulder_off[1])
    is_active_arm = not is_left
    angle = pose["left_arm_rotation" if is_left else "right_arm_rotation"] * facing
    if pose.get("hand_on_chin") and is_active_arm:
        angle = -150 * facing
    if pose.get("thumbs_up") and is_active_arm:
        angle = -170 * facing
    elbow = _pt(shoulder, angle * 0.55, UPPER_ARM_LEN * scale)
    hand = _pt(elbow, angle * 1.2, FOREARM_LEN * scale)
    return shoulder, elbow, hand, angle


def hand_point(pose, side="left"):
    """Public helper: where a prop should attach to that hand."""
    return _arm_geometry(pose, side)[2]


def _leg_geometry(pose, side):
    scale = pose.get("scale", 1.0)
    facing = pose.get("facing", 1)
    hip = (pose["x"], pose["y"])
    thigh_len = THIGH_LEN * scale * (1 - 0.3 * pose.get("crouch", 0.0))
    shin_len = SHIN_LEN * scale * (1 - 0.3 * pose.get("crouch", 0.0))
    is_left = side == "left"
    hip_off = (-17 * scale * facing if is_left else 17 * scale * facing, 0)
    origin = (hip[0] + hip_off[0], hip[1] + hip_off[1])
    rot = pose["left_leg_rotation" if is_left else "right_leg_rotation"] * facing
    knee = _pt(origin, rot * 0.5, thigh_len)
    ankle = _pt(knee, rot * 1.3, shin_len)
    return origin, knee, ankle, rot


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


def _draw_hand(draw, hand, angle, facing, gloved=True):
    color = GLOVE if gloved else SKIN
    r = HAND_R
    draw.ellipse([hand[0] - r, hand[1] - r * 0.85, hand[0] + r, hand[1] + r * 0.85], fill=color)
    thumb = _pt(hand, angle - 55 * facing, r * 0.9)
    tr = r * 0.55
    draw.ellipse([thumb[0] - tr, thumb[1] - tr, thumb[0] + tr, thumb[1] + tr], fill=color)


def draw_character(canvas: Image.Image, pose: dict):
    draw = ImageDraw.Draw(canvas, "RGBA")
    scale = pose.get("scale", 1.0)
    facing = pose.get("facing", 1)
    hip = (pose["x"], pose["y"])

    # --- glow halo (bend correct/wrong, leg highlight during lift) ---
    if pose.get("glow_color") and pose.get("glow_intensity", 0) > 0:
        glow = hex_to_rgb(pose["glow_color"])
        alpha = int(90 * pose["glow_intensity"])
        r = 150 * scale
        draw.ellipse([hip[0] - r, hip[1] - r * 1.3, hip[0] + r, hip[1] + r * 1.1],
                     fill=(*glow, alpha))

    # --- legs (denim, two segments with a knee) + sneakers ---
    leg_pts = {}
    for side in ("left", "right"):
        origin, knee, ankle, rot = _leg_geometry(pose, side)
        leg_pts[side] = ankle
        _capsule(draw, origin, knee, LEG_WIDTH * scale, OVERALLS)
        _capsule(draw, knee, ankle, LEG_WIDTH * scale * 0.92, OVERALLS)
        # ankle cuff
        cuff = _pt(knee, rot * 1.3, SHIN_LEN * scale * 0.8)
        _capsule(draw, cuff, ankle, LEG_WIDTH * scale, OVERALLS_DARK)

        bx, by = ankle
        sw, sh = SHOE_WIDTH * scale, SHOE_HEIGHT * scale
        draw.rounded_rectangle([bx - sw / 2, by - sh * 0.3, bx + sw / 2, by + sh * 0.7],
                                radius=sh * 0.4, fill=SHOE_COLOR, outline=SHOE_DARK,
                                width=max(1, int(2 * scale)))
        draw.rounded_rectangle([bx - sw / 2, by + sh * 0.35, bx + sw / 2, by + sh * 0.7],
                                radius=sh * 0.25, fill=SHOE_SOLE)

    if pose.get("leg_glow_color") and pose.get("leg_glow_intensity", 0) > 0:
        glow = hex_to_rgb(pose["leg_glow_color"])
        alpha = int(120 * pose["leg_glow_intensity"])
        r = 55 * scale
        draw.ellipse([hip[0] - r, hip[1], hip[0] + r, max(leg_pts["left"][1], leg_pts["right"][1])],
                     outline=(*glow, alpha), width=6)

    # --- torso: white tee, blue denim overalls bib + straps on top ---
    torso_len = TORSO_HEIGHT * scale
    neck = _pt(hip, pose["torso_rotation"] * facing, -torso_len)
    _capsule(draw, hip, neck, TORSO_WIDTH * scale, SHIRT)

    bib_top = _pt(hip, pose["torso_rotation"] * facing, -torso_len * 0.62)
    _capsule(draw, hip, bib_top, TORSO_WIDTH * scale * 0.92, OVERALLS)
    _highlight(canvas, hip[0] - TORSO_WIDTH * scale * 0.18,
               hip[1] - torso_len * 0.45, TORSO_WIDTH * scale * 0.22, torso_len * 0.22,
               OVERALLS_LIGHT, alpha=100, blur=8)

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
        strap_top = (neck[0] + sign * 20 * scale, neck[1] + 4 * scale)
        draw.line([strap_bottom, strap_top], fill=OVERALLS, width=max(3, int(10 * scale)))
        br = 4 * scale
        draw.ellipse([strap_bottom[0] - br, strap_bottom[1] - br,
                      strap_bottom[0] + br, strap_bottom[1] + br], fill=OVERALLS_BUTTON)

    # --- arms (two segments with an elbow) ---
    for side in ("left", "right"):
        is_active_arm = (side == "right")
        shoulder, elbow, hand, angle = _arm_geometry(pose, side)
        _capsule(draw, shoulder, elbow, ARM_WIDTH * scale, SHIRT)
        _capsule(draw, elbow, hand, ARM_WIDTH * scale * 0.9, SKIN)
        _draw_hand(draw, hand, angle, facing)
        if pose.get("thumbs_up") and is_active_arm:
            tip = _pt(hand, angle - 70 * facing, 24 * scale)
            _capsule(draw, hand, tip, 9 * scale, GLOVE)

    # --- head ---
    hr = HEAD_RADIUS * scale
    head_c = _pt(neck, pose["torso_rotation"] * facing + pose.get("head_tilt", 0) * facing, -hr * 0.85)
    hx, hy = head_c

    # hair: a back halo (peeks above/behind the face), short front bangs, and
    # a single ponytail swept to one side and hanging past the shoulder.
    draw.ellipse([hx - hr * 1.1, hy - hr * 1.1, hx + hr * 1.1, hy + hr * 0.55], fill=HAIR)

    # opposite side from the (usually active) right arm, so waves/gestures
    # don't swing straight through the hair
    ponytail_side = -facing
    tie = (hx + ponytail_side * hr * 0.98, hy - hr * 0.1)
    tail_end = (hx + ponytail_side * hr * 1.5, hy + hr * 1.6)
    tail_mid = (hx + ponytail_side * hr * 1.7, hy + hr * 0.7)
    draw.line([tie, tail_mid, tail_end], fill=HAIR, width=int(hr * 0.4), joint="curve")
    r_end = hr * 0.13
    draw.ellipse([tail_end[0] - r_end, tail_end[1] - r_end, tail_end[0] + r_end, tail_end[1] + r_end],
                 fill=HAIR)

    # face
    draw.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=SKIN)
    _highlight(canvas, hx - hr * 0.4, hy - hr * 0.5, hr * 0.45, hr * 0.4, SKIN_LIGHT, alpha=110, blur=9)

    # short front bangs
    draw.pieslice([hx - hr * 0.95, hy - hr * 1.05, hx + hr * 0.95, hy - hr * 0.15],
                  start=180, end=360, fill=HAIR)
    _highlight(canvas, hx + hr * 0.3, hy - hr * 0.85, hr * 0.35, hr * 0.18, HAIR_LIGHT, alpha=90, blur=5)

    # hair tie band at the base of the ponytail
    tie_r = hr * 0.16
    draw.ellipse([tie[0] - tie_r, tie[1] - tie_r, tie[0] + tie_r, tie[1] + tie_r], fill=HAIR_TIE)

    # blush
    for sign in (-1, 1):
        bx = hx + sign * hr * 0.55
        by = hy + hr * 0.18
        br = hr * 0.17
        draw.ellipse([bx - br, by - br, bx + br, by + br], fill=(*BLUSH, 140))

    # eyebrows
    expression = pose.get("expression", "smile")
    brow_lift = -4 if expression in ("determined", "focused") else 0
    for sign in (-1, 1):
        bx = hx + sign * hr * 0.38
        by = hy - hr * 0.42 + brow_lift
        draw.arc([bx - hr * 0.18, by - hr * 0.08, bx + hr * 0.18, by + hr * 0.1],
                  start=200, end=340, fill=HAIR, width=max(2, int(3 * scale)))

    # eyes: big glossy dark irises with a bright catchlight
    for sign in (-1, 1):
        ex = hx + sign * hr * 0.38
        ey = hy - hr * 0.02
        ew, eh = hr * 0.26, hr * 0.3
        draw.ellipse([ex - ew, ey - eh, ex + ew, ey + eh], fill=EYE_WHITE)
        ir = ew * 0.78
        ix = ex + sign * ew * 0.05
        draw.ellipse([ix - ir, ey - ir * 1.05, ix + ir, ey + ir * 1.05], fill=EYE_IRIS)
        gr = ir * 0.32
        draw.ellipse([ix - gr * 1.6, ey - ir * 0.7, ix - gr * 0.2, ey - ir * 0.7 + gr * 1.6],
                     fill=EYE_WHITE)

    # mouth
    mouth_curve = {
        "smile": 9, "proud_smile": 13, "thoughtful": 3, "determined": 2,
        "focused": 4, "satisfied": 11, "careful": 4, "thumbs_up": 13,
    }.get(expression, 8)
    mw = hr * 0.42
    my = hy + hr * 0.5
    draw.arc([hx - mw, my - mouth_curve, hx + mw, my + mouth_curve], start=20, end=160,
              fill=MOUTH, width=max(2, int(3 * scale)))

    return canvas
