#!/usr/bin/env python3
"""Renders "Safe Manual Handling for Cleaners" from spec/scenes.json.

Examples:
    python3 generate_video.py                     # full 180s render at 1920x1080/24fps
    python3 generate_video.py --preview            # fast low-res smoke test
    python3 generate_video.py --start 0 --end 20   # render just scene 1
    python3 generate_video.py --no-audio           # skip audio mixing
"""
import argparse
import sys

import numpy as np
from PIL import Image

from render import WIDTH, HEIGHT, FPS, METADATA, render_frame


def make_frame_factory(scale, t_offset):
    out_w, out_h = int(WIDTH * scale), int(HEIGHT * scale)

    def make_frame(t):
        frame_idx = int(round((t + t_offset) * FPS))
        arr = render_frame(frame_idx)
        if scale != 1.0:
            arr = np.array(Image.fromarray(arr).resize((out_w, out_h), Image.BILINEAR))
        return arr

    return make_frame, out_w, out_h


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", default="output/safe_manual_handling.mp4")
    parser.add_argument("--start", type=float, default=0.0, help="start time in seconds")
    parser.add_argument("--end", type=float, default=None, help="end time in seconds")
    parser.add_argument("--preview", action="store_true", help="0.25x resolution, faster encode")
    parser.add_argument("--scale", type=float, default=None, help="explicit resolution scale")
    parser.add_argument("--no-audio", action="store_true")
    args = parser.parse_args()

    end = args.end if args.end is not None else METADATA["duration_seconds"]
    duration = end - args.start
    if duration <= 0:
        sys.exit("end must be greater than start")

    scale = args.scale if args.scale is not None else (0.25 if args.preview else 1.0)

    from moviepy import VideoClip

    make_frame, out_w, out_h = make_frame_factory(scale, args.start)
    clip = VideoClip(make_frame, duration=duration).with_fps(FPS)

    if not args.no_audio:
        import audio as audio_module
        stereo = audio_module.build_audio_track()
        sr = audio_module.SAMPLE_RATE
        start_sample = int(args.start * sr)
        end_sample = int(end * sr)
        segment = stereo[start_sample:end_sample]
        if len(segment) > 0:
            from moviepy import AudioArrayClip
            clip = clip.with_audio(AudioArrayClip(segment, fps=sr))

    print(f"Rendering {duration:.1f}s @ {out_w}x{out_h}, {FPS}fps -> {args.output}")
    clip.write_videofile(
        args.output,
        fps=FPS,
        codec="libx264",
        audio_codec="aac" if not args.no_audio else None,
        bitrate=None if scale != 1.0 else METADATA["bitrate_video"],
        audio_bitrate=METADATA["bitrate_audio"] if not args.no_audio else None,
        audio_fps=METADATA["sample_rate_audio"] if not args.no_audio else None,
        preset="ultrafast" if args.preview else "medium",
        threads=4,
    )


if __name__ == "__main__":
    main()
