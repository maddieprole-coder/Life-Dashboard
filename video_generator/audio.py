"""Builds the audio track: synthesized sound effects (Section 7) mixed with
optional external voiceover / music assets.

No TTS engine or licensed music library is available in this environment,
so voiceover and background music are NOT fabricated here. If real files
are dropped into `audio_assets/` using the exact names from spec/scenes.json
(`voiceover.audio_file`, e.g. `voiceover_scene_1.mp3`, and
`bgm_scene_<scene_id>.mp3` for background_music), they are mixed in at the
correct offsets and volumes. Otherwise those channels stay silent and only
the synthesized sound effects (whoosh, dings, chimes, footsteps, ...) play.
"""
import json
import math
import os

import numpy as np

from render import METADATA, SCENES, FPS

SAMPLE_RATE = METADATA["sample_rate_audio"]
DURATION_S = METADATA["duration_seconds"]
AUDIO_DIR = os.path.join(os.path.dirname(__file__), "audio_assets")

SFX_PARAMS = {
    "whoosh": dict(freq=300, kind="noise_sweep"),
    "lifting_whoosh": dict(freq=250, kind="noise_sweep"),
    "gentle_lowering": dict(freq=200, kind="noise_sweep"),
    "positive_ding": dict(freq=880, kind="tone"),
    "success_tone": dict(freq=990, kind="tone"),
    "alert_sound": dict(freq=660, kind="tone"),
    "muscle_activation": dict(freq=150, kind="tone"),
    "click": dict(freq=1200, kind="click"),
    "warning_buzzer": dict(freq=220, kind="buzz"),
    "footsteps": dict(freq=100, kind="thud_repeat"),
    "completion_chime": dict(freq=1046.5, kind="chime"),
    "success_fanfare": dict(freq=523.25, kind="chime"),
}


def _hann(n):
    if n <= 1:
        return np.ones(max(n, 1))
    return 0.5 - 0.5 * np.cos(2 * math.pi * np.arange(n) / (n - 1))


def _tone(n, freq, sr=SAMPLE_RATE):
    t = np.arange(n) / sr
    return np.sin(2 * math.pi * freq * t) * _hann(n)


def _buzz(n, freq, sr=SAMPLE_RATE):
    t = np.arange(n) / sr
    wave = np.sign(np.sin(2 * math.pi * freq * t))
    return wave * _hann(n) * 0.6


def _click(n, freq, sr=SAMPLE_RATE):
    noise = np.random.uniform(-1, 1, n)
    env = np.exp(-np.linspace(0, 12, n))
    return noise * env


def _noise_sweep(n, freq, sr=SAMPLE_RATE):
    t = np.arange(n) / sr
    sweep_freq = np.linspace(freq * 1.6, freq * 0.5, n)
    tone = np.sin(2 * math.pi * np.cumsum(sweep_freq) / sr)
    noise = np.random.uniform(-1, 1, n)
    return (0.6 * tone + 0.4 * noise) * _hann(n)


def _chime(n, freq, sr=SAMPLE_RATE):
    t = np.arange(n) / sr
    env = np.exp(-np.linspace(0, 5, n))
    wave = np.zeros(n)
    for mult, amp in ((1, 1.0), (1.5, 0.5), (2, 0.3)):
        wave += amp * np.sin(2 * math.pi * freq * mult * t)
    return wave * env


def _thud_repeat(n, freq, sr=SAMPLE_RATE):
    wave = np.zeros(n)
    step = int(sr * 0.35)
    thud_len = int(sr * 0.08)
    for start in range(0, n, step):
        end = min(start + thud_len, n)
        length = end - start
        if length <= 0:
            continue
        env = np.exp(-np.linspace(0, 20, length))
        t = np.arange(length) / sr
        wave[start:end] += np.sin(2 * math.pi * freq * t) * env
    return wave


_GENERATORS = {
    "tone": _tone, "buzz": _buzz, "click": _click,
    "noise_sweep": _noise_sweep, "chime": _chime, "thud_repeat": _thud_repeat,
}


def synth_effect(effect_type, duration_frames, volume=0.7):
    n = max(1, int(duration_frames / FPS * SAMPLE_RATE))
    params = SFX_PARAMS.get(effect_type, dict(freq=440, kind="tone"))
    gen = _GENERATORS[params["kind"]]
    wave = gen(n, params["freq"]) * volume
    return wave.astype(np.float32)


def build_audio_track():
    total_samples = int(DURATION_S * SAMPLE_RATE)
    track = np.zeros(total_samples, dtype=np.float32)

    for scene in SCENES:
        for sfx in scene.get("sound_effects", []):
            frame = sfx["frame"]
            start_sample = int(frame / FPS * SAMPLE_RATE)
            wave = synth_effect(sfx["type"], sfx.get("duration_frames", 20), sfx.get("volume", 0.7))
            end_sample = min(total_samples, start_sample + len(wave))
            if start_sample < total_samples:
                track[start_sample:end_sample] += wave[: end_sample - start_sample]

        vo = scene.get("voiceover")
        if vo:
            _mix_external_file(track, os.path.join(AUDIO_DIR, vo["audio_file"]),
                                vo["start_frame"], volume=1.0, sr=total_samples)

        bgm = scene.get("background_music")
        if bgm and bgm.get("volume", 0) > 0:
            bgm_file = os.path.join(AUDIO_DIR, f"bgm_scene_{scene['scene_id']}.mp3")
            _mix_external_file(track, bgm_file, bgm["start_frame"], volume=bgm["volume"],
                                sr=total_samples)

    np.clip(track, -1.0, 1.0, out=track)
    stereo = np.stack([track, track], axis=1)
    return stereo


def _mix_external_file(track, path, start_frame, volume, sr):
    if not os.path.exists(path):
        return
    try:
        from moviepy import AudioFileClip
    except ImportError:
        return
    clip = AudioFileClip(path)
    samples = clip.to_soundarray(fps=SAMPLE_RATE)
    if samples.ndim > 1:
        samples = samples.mean(axis=1)
    samples = samples * volume
    start_sample = int(start_frame / FPS * SAMPLE_RATE)
    end_sample = min(len(track), start_sample + len(samples))
    if start_sample < len(track):
        track[start_sample:end_sample] += samples[: end_sample - start_sample].astype(np.float32)
    clip.close()
