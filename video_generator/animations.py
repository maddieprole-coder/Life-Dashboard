"""Pose generators for each `animation` name used in spec/scenes.json.

These translate the keyframes in spec Section 4 (character_main.animations)
and the pseudocode in spec Section 6 into per-frame pose dicts consumed by
character.draw_character().
"""
from character import default_pose
from easing import ease_out, sine_wave, sine_cycle, lerp, progress as prog


def _keyframe(frame, points):
    """Piecewise-linear interpolation over [(frame, value), ...] (Section 4 style)."""
    if frame <= points[0][0]:
        return points[0][1]
    if frame >= points[-1][0]:
        return points[-1][1]
    for (f0, v0), (f1, v1) in zip(points, points[1:]):
        if f0 <= frame <= f1:
            t = (frame - f0) / (f1 - f0) if f1 != f0 else 1
            return lerp(v0, v1, t)
    return points[-1][1]


def pose_wave_friendly(frame, duration, x, y, **_):
    # Section 4: right_arm rotation keyframes 0:0 120:-90 240:-60 360:-90 480:0
    angle = _keyframe(frame, [(0, 0), (120, -90), (240, -60), (360, -90), (480, 0)])
    return default_pose(x=x, y=y, right_arm_rotation=angle, expression="smile")


def pose_assess_load(frame, duration, x, y, hand_on_chin=False, **_):
    head_tilt = _keyframe(frame, [(100, -15), (300, 15), (500, -15)])
    return default_pose(x=x, y=y, head_tilt=head_tilt, hand_on_chin=hand_on_chin,
                         expression="thoughtful")


def pose_position_feet(frame, duration, x, y, look_down=False, **_):
    left = _keyframe(frame, [(0, -20), (300, -30), (600, -30)])
    right = _keyframe(frame, [(0, 20), (150, 15), (600, 15)])
    return default_pose(x=x, y=y, left_leg_rotation=left, right_leg_rotation=right,
                         head_tilt=10 if look_down else 0, expression="focused")


def pose_bend(frame, duration, x, y, style="correct", **_):
    # Section 6 animate_bend(): correct keeps spine straight, bends knees; wrong bends spine.
    t = prog(frame, 0, duration)
    if style == "correct":
        torso = 0
        knee = sine_wave(t) * 60
        glow = ("#00AA00", 0.6)
    else:
        torso = sine_wave(t) * 45
        knee = sine_wave(t) * 15
        glow = ("#FF4444", 0.6)
    return default_pose(x=x, y=y, torso_rotation=torso,
                         left_leg_rotation=knee, right_leg_rotation=knee,
                         crouch=knee / 90, glow_color=glow[0], glow_intensity=glow[1],
                         expression="focused" if style == "correct" else "determined")


def pose_grip_and_lift(frame, duration, x, y, leg_glow_color=None, leg_glow_intensity=0.0, **_):
    # Section 6 animate_lift(): character crouches then stands, legs highlighted.
    t = prog(frame, 0, duration)
    e = ease_out(t)
    crouch = lerp(0.55, 0.0, e)
    y_pos = lerp(y + 60, y, e)
    return default_pose(x=x, y=y_pos, crouch=crouch,
                         left_leg_rotation=lerp(45, 0, e), right_leg_rotation=lerp(45, 0, e),
                         leg_glow_color=leg_glow_color, leg_glow_intensity=leg_glow_intensity,
                         expression="determined")


def pose_walk_with_bucket(frame, duration, x0, y0, x1, y1, **_):
    # Section 6 animate_walk(): x lerps across the scene, legs cycle in a walking gait.
    t = prog(frame, 0, duration)
    x = lerp(x0, x1, t)
    cycle = (frame % 60) / 60
    left = sine_cycle(cycle) * 20
    right = -sine_cycle(cycle) * 20
    return default_pose(x=x, y=y0, left_leg_rotation=left, right_leg_rotation=right,
                         expression="focused")


def pose_bend_and_set_down(frame, duration, x, y, **_):
    # Reverse of grip_and_lift: crouches to place the bucket down, then stands.
    t = prog(frame, 0, duration)
    e = ease_out(t)
    crouch = lerp(0.0, 0.55, e) if t < 0.75 else lerp(0.55, 0.0, (t - 0.75) / 0.25)
    return default_pose(x=x, y=y, crouch=crouch,
                         left_leg_rotation=crouch * 80, right_leg_rotation=crouch * 80,
                         expression="careful")


def pose_thumbs_up_confident(frame, duration, x, y, **_):
    return default_pose(x=x, y=y, thumbs_up=True, expression="proud_smile")


ANIMATIONS = {
    "wave_friendly": pose_wave_friendly,
    "assess_load": pose_assess_load,
    "position_feet": pose_position_feet,
    "grip_and_lift": pose_grip_and_lift,
    "walk_with_bucket": pose_walk_with_bucket,
    "bend_and_set_down": pose_bend_and_set_down,
    "thumbs_up_confident": pose_thumbs_up_confident,
}


def get_pose(anim_name, frame, duration, element):
    pos = element.get("position", {"x": 960, "y": 560})
    fn = ANIMATIONS.get(anim_name)
    if fn is None:
        return default_pose(x=pos["x"], y=pos["y"])
    kwargs = dict(
        x=pos["x"], y=pos["y"],
        hand_on_chin=element.get("hand_on_chin", False),
        look_down=element.get("look_down", False),
        leg_glow_color=element.get("leg_glow_color"),
        leg_glow_intensity=element.get("leg_glow_intensity", 0.0),
    )
    if anim_name == "walk_with_bucket":
        start = element.get("start_position", pos)
        end = element.get("end_position", pos)
        kwargs.update(x0=start["x"], y0=start["y"], x1=end["x"], y1=end["y"])
    return fn(frame, duration, **kwargs)
