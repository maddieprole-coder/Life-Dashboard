"""Interpolation and easing helpers used by the frame renderer."""
import math


def clamp01(t: float) -> float:
    return 0.0 if t < 0 else 1.0 if t > 1 else t


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * clamp01(t)


def ease_in(t: float) -> float:
    t = clamp01(t)
    return t * t


def ease_out(t: float) -> float:
    t = clamp01(t)
    return 1 - (1 - t) * (1 - t)


def ease_in_out(t: float) -> float:
    t = clamp01(t)
    return t * t * (3 - 2 * t)


def sine_wave(t: float) -> float:
    """Smooth 0 -> 1 rise, matching the spec's `sine_wave(progress)` calls."""
    return math.sin(clamp01(t) * math.pi / 2)


def sine_cycle(t: float) -> float:
    """Repeating -1..1 wave for cyclic motion (e.g. walking gait)."""
    return math.sin(t * 2 * math.pi)


def progress(frame: float, start_frame: float, duration_frames: float) -> float:
    if duration_frames <= 0:
        return 1.0
    return clamp01((frame - start_frame) / duration_frames)


def hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
