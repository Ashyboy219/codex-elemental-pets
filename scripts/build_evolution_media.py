#!/usr/bin/env python3
"""Build the visual-first social cut for the Elemental Pets Ultra proposal."""

from __future__ import annotations

import math
import shutil
import subprocess
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from build_media import (
    FONT_BOLD,
    FONT_MONO,
    FONT_REGULAR,
    add_particles,
    background,
    draw_centered,
    draw_chip,
    draw_sprite,
    font,
    smoothstep,
)


ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / "media"
DOCS_ASSETS = ROOT / "docs" / "assets"
FPS = 24
DURATION = 18.0


def scene_fade(t: float, start: float, end: float, edge: float = 0.24) -> float:
    return smoothstep((t - start) / edge) * smoothstep((end - t) / edge)


def load_ultra(name: str) -> Image.Image:
    candidates = (
        MEDIA / f"{name}-ultra.png",
        DOCS_ASSETS / f"{name}-ultra.png",
    )
    for path in candidates:
        if path.exists():
            return Image.open(path).convert("RGBA")
    raise FileNotFoundError(
        f"Missing {name} Ultra art. Expected one of: "
        + ", ".join(str(path) for path in candidates)
    )


def contain(image: Image.Image, box: tuple[int, int]) -> Image.Image:
    fitted = image.copy()
    fitted.thumbnail(box, Image.Resampling.NEAREST)
    return fitted


def draw_ultra(
    canvas: Image.Image,
    art: Image.Image,
    center_x: int,
    baseline_y: int,
    box: tuple[int, int],
) -> tuple[int, int, int, int]:
    target = contain(art, box)
    x = int(center_x - target.width / 2)
    y = int(baseline_y - target.height)
    canvas.alpha_composite(target, (x, y))
    return x, y, target.width, target.height


def install_card(canvas: Image.Image, box: tuple[int, int, int, int]) -> None:
    """Draw a privacy-safe settings cue without reproducing third-party UI art."""
    x, y, width, height = box
    panel = Image.new("RGBA", (width, height), (31, 32, 35, 248))
    panel_draw = ImageDraw.Draw(panel, "RGBA")
    panel_draw.rounded_rectangle((0, 0, panel.width - 1, panel.height - 1), radius=18, fill=(13, 18, 31, 238), outline=(174, 199, 232, 72), width=2)
    pad = max(18, int(height * 0.14))
    title_font = font(FONT_BOLD, max(16, int(height * 0.20)))
    path_font = font(FONT_MONO, max(13, int(height * 0.15)))
    action_font = font(FONT_REGULAR, max(14, int(height * 0.17)))
    panel_draw.text((pad, pad), "Custom pets", font=title_font, fill=(247, 249, 252, 255))
    panel_draw.text((pad, int(height * 0.57)), "~/.codex/pets", font=path_font, fill=(183, 191, 207, 255))
    action = "Open folder  ↗"
    action_box = panel_draw.textbbox((0, 0), action, font=action_font)
    panel_draw.text((width - pad - (action_box[2] - action_box[0]), int(height * 0.39)), action, font=action_font, fill=(204, 210, 220, 255))
    canvas.alpha_composite(panel, (x, y))


def render_frame(width: int, height: int, t: float, vertical: bool, frost_ultra: Image.Image, bolt_ultra: Image.Image) -> Image.Image:
    image = background(width, height)
    # Keep the complete evolved-form scene still, including its atmosphere.
    particle_time = 9.5 if 9.5 <= t < 13.2 else t
    add_particles(image, particle_time)
    draw = ImageDraw.Draw(image, "RGBA")
    scale = width / (720 if vertical else 1280)
    safe = int(34 * scale)
    draw_chip(draw, (safe, safe), "UNOFFICIAL COMMUNITY PETS", scale)

    if t < 2.6:
        # The first frame is the thumbnail/hook, so it must land immediately.
        alpha = smoothstep((2.6 - t) / 0.18)
        title = font(FONT_BOLD, int((69 if vertical else 70) * scale))
        sub = font(FONT_MONO, int((19 if vertical else 21) * scale))
        top = int((150 if vertical else 78) * scale)
        draw_centered(draw, top, "I HATCHED TWO", title, (245, 249, 255, int(255 * alpha)), width, stroke=max(1, int(2 * scale)), stroke_fill=(3, 6, 14, 210))
        draw_centered(draw, top + int(80 * scale), "CODEX ELEMENTS", title, (255, 220, 71, int(255 * alpha)), width, stroke=max(1, int(2 * scale)), stroke_fill=(3, 6, 14, 210))
        draw_centered(draw, top + int(178 * scale), "FROSTBYTE  ×  BOLT", sub, (167, 219, 245, int(238 * alpha)), width)
        baseline = int((1030 if vertical else 670) * scale)
        if vertical:
            draw_sprite(image, "frostbyte", "jumping", t, int(width * 0.28), baseline, 1.63 * scale, alpha)
            draw_sprite(image, "bolt", "jumping", t + 0.2, int(width * 0.72), baseline, 1.63 * scale, alpha)
        else:
            draw_sprite(image, "frostbyte", "jumping", t, int(width * 0.34), baseline, 2.05 * scale, alpha)
            draw_sprite(image, "bolt", "jumping", t + 0.2, int(width * 0.66), baseline, 2.05 * scale, alpha)

    elif t < 6.0:
        local = t - 2.6
        alpha = scene_fade(t, 2.6, 6.0)
        body = font(FONT_REGULAR, int((23 if vertical else 24) * scale))
        top = int((142 if vertical else 64) * scale)
        if vertical:
            title = font(FONT_BOLD, int(52 * scale))
            draw_centered(draw, top, "THEY WORK WHILE", title, (246, 249, 255, int(255 * alpha)), width, stroke=max(1, int(2 * scale)), stroke_fill=(3, 6, 14, 210))
            draw_centered(draw, top + int(59 * scale), "CODEX WORKS", title, (246, 249, 255, int(255 * alpha)), width, stroke=max(1, int(2 * scale)), stroke_fill=(3, 6, 14, 210))
            draw_centered(draw, top + int(132 * scale), "Snowcraft precision  ×  charged-console speed", body, (185, 211, 241, int(238 * alpha)), width)
        else:
            title = font(FONT_BOLD, int(58 * scale))
            draw_centered(draw, top, "THEY WORK WHILE CODEX WORKS", title, (246, 249, 255, int(255 * alpha)), width, stroke=max(1, int(2 * scale)), stroke_fill=(3, 6, 14, 210))
            draw_centered(draw, top + int(74 * scale), "Snowcraft precision  ×  charged-console speed", body, (185, 211, 241, int(238 * alpha)), width)
        baseline = int((1015 if vertical else 675) * scale)
        if vertical:
            draw_sprite(image, "frostbyte", "running", local, int(width * 0.28), baseline, 1.55 * scale, alpha)
            draw_sprite(image, "bolt", "running", local + 0.13, int(width * 0.72), baseline, 1.55 * scale, alpha)
        else:
            draw_sprite(image, "frostbyte", "running", local, int(width * 0.32), baseline, 2.1 * scale, alpha)
            draw_sprite(image, "bolt", "running", local + 0.13, int(width * 0.68), baseline, 2.1 * scale, alpha)

    elif t < 9.5:
        local = t - 6.0
        alpha = scene_fade(t, 6.0, 9.5)
        sub = font(FONT_MONO, int((18 if vertical else 20) * scale))
        top = int((142 if vertical else 62) * scale)
        if vertical:
            title = font(FONT_BOLD, int(58 * scale))
            draw_centered(draw, top, "NOW IMAGINE", title, (245, 248, 255, int(255 * alpha)), width, stroke=max(1, int(2 * scale)), stroke_fill=(3, 6, 14, 210))
            draw_centered(draw, top + int(65 * scale), "ULTRA MODE", title, (245, 248, 255, int(255 * alpha)), width, stroke=max(1, int(2 * scale)), stroke_fill=(3, 6, 14, 210))
            draw_centered(draw, top + int(143 * scale), "UPSTREAM FEATURE CONCEPT", sub, (255, 219, 69, int(242 * alpha)), width)
        else:
            title = font(FONT_BOLD, int(67 * scale))
            draw_centered(draw, top, "NOW IMAGINE ULTRA MODE", title, (245, 248, 255, int(255 * alpha)), width, stroke=max(1, int(2 * scale)), stroke_fill=(3, 6, 14, 210))
            draw_centered(draw, top + int(84 * scale), "UPSTREAM FEATURE CONCEPT", sub, (255, 219, 69, int(242 * alpha)), width)
        baseline = int((1050 if vertical else 690) * scale)
        if vertical:
            draw_sprite(image, "frostbyte", "idle", local, int(width * 0.28), baseline, 1.55 * scale, alpha)
            draw_sprite(image, "bolt", "idle", local + 0.1, int(width * 0.72), baseline, 1.55 * scale, alpha)
        else:
            draw_sprite(image, "frostbyte", "idle", local, int(width * 0.32), baseline, 2.0 * scale, alpha)
            draw_sprite(image, "bolt", "idle", local + 0.1, int(width * 0.68), baseline, 2.0 * scale, alpha)

    elif t < 13.2:
        # This is intentionally a hard cut to a fully static evolved-form card.
        alpha = 1.0
        sub = font(FONT_MONO, int((18 if vertical else 20) * scale))
        top = int((138 if vertical else 58) * scale)
        if vertical:
            title = font(FONT_BOLD, int(62 * scale))
            draw_centered(draw, top, "EVOLVED", title, (247, 249, 255, int(255 * alpha)), width, stroke=max(1, int(2 * scale)), stroke_fill=(3, 6, 14, 210))
            draw_centered(draw, top + int(69 * scale), "FORMS", title, (247, 249, 255, int(255 * alpha)), width, stroke=max(1, int(2 * scale)), stroke_fill=(3, 6, 14, 210))
            draw_centered(draw, top + int(149 * scale), "SAME FACE. VERY DIFFERENT EMOTION.", sub, (175, 213, 241, int(238 * alpha)), width)
        else:
            title = font(FONT_BOLD, int(66 * scale))
            draw_centered(draw, top, "EVOLVED FORMS", title, (247, 249, 255, int(255 * alpha)), width, stroke=max(1, int(2 * scale)), stroke_fill=(3, 6, 14, 210))
            draw_centered(draw, top + int(82 * scale), "SAME FACE. VERY DIFFERENT EMOTION.", sub, (175, 213, 241, int(238 * alpha)), width)
        baseline = int((1050 if vertical else 700) * scale)
        if vertical:
            draw_ultra(image, frost_ultra, int(width * 0.29), baseline, (int(265 * scale), int(620 * scale)))
            draw_ultra(image, bolt_ultra, int(width * 0.71), baseline, (int(265 * scale), int(620 * scale)))
        else:
            draw_ultra(image, frost_ultra, int(width * 0.32), baseline, (int(360 * scale), int(620 * scale)))
            draw_ultra(image, bolt_ultra, int(width * 0.68), baseline, (int(360 * scale), int(620 * scale)))

    elif t < 15.8:
        alpha = scene_fade(t, 13.2, 15.8)
        body = font(FONT_REGULAR, int((22 if vertical else 24) * scale))
        mono = font(FONT_MONO, int((17 if vertical else 19) * scale))
        top = int((128 if vertical else 52) * scale)
        if vertical:
            title = font(FONT_BOLD, int(52 * scale))
            draw_centered(draw, top, "OFFICIAL CUSTOM-PET", title, (246, 249, 255, int(255 * alpha)), width, stroke=max(1, int(2 * scale)), stroke_fill=(3, 6, 14, 210))
            draw_centered(draw, top + int(59 * scale), "FLOW", title, (246, 249, 255, int(255 * alpha)), width, stroke=max(1, int(2 * scale)), stroke_fill=(3, 6, 14, 210))
            draw_centered(draw, top + int(130 * scale), "SETTINGS  >  PETS  >  OPEN FOLDER", mono, (255, 220, 71, int(245 * alpha)), width)
            draw_centered(draw, top + int(174 * scale), "Copy the pet folders, Refresh, then select.", body, (182, 207, 236, int(238 * alpha)), width)
        else:
            title = font(FONT_BOLD, int(62 * scale))
            draw_centered(draw, top, "OFFICIAL CUSTOM-PET FLOW", title, (246, 249, 255, int(255 * alpha)), width, stroke=max(1, int(2 * scale)), stroke_fill=(3, 6, 14, 210))
            draw_centered(draw, top + int(76 * scale), "SETTINGS  >  PETS  >  OPEN FOLDER", mono, (255, 220, 71, int(245 * alpha)), width)
            draw_centered(draw, top + int(121 * scale), "Copy the pet folders, Refresh, then select.", body, (182, 207, 236, int(238 * alpha)), width)
        if vertical:
            install_card(image, (int(45 * scale), int(410 * scale), int(630 * scale), int(160 * scale)))
            draw_sprite(image, "frostbyte", "waving", t, int(width * 0.30), int(1030 * scale), 1.35 * scale, alpha)
            draw_sprite(image, "bolt", "waving", t + 0.2, int(width * 0.70), int(1030 * scale), 1.35 * scale, alpha)
        else:
            install_card(image, (int(110 * scale), int(250 * scale), int(1060 * scale), int(150 * scale)))
            draw_sprite(image, "frostbyte", "waving", t, int(width * 0.23), int(690 * scale), 1.6 * scale, alpha)
            draw_sprite(image, "bolt", "waving", t + 0.2, int(width * 0.77), int(690 * scale), 1.6 * scale, alpha)

    else:
        local = t - 15.8
        alpha = scene_fade(t, 15.8, 18.0, 0.18)
        body = font(FONT_REGULAR, int((23 if vertical else 25) * scale))
        mono = font(FONT_MONO, int((16 if vertical else 19) * scale))
        top = int((128 if vertical else 58) * scale)
        if vertical:
            title = font(FONT_BOLD, int(54 * scale))
            draw_centered(draw, top, "OPENAI — LET'S", title, (246, 249, 255, int(255 * alpha)), width, stroke=max(1, int(2 * scale)), stroke_fill=(3, 6, 14, 210))
            draw_centered(draw, top + int(62 * scale), "EVOLVE PETS.", title, (246, 249, 255, int(255 * alpha)), width, stroke=max(1, int(2 * scale)), stroke_fill=(3, 6, 14, 210))
            draw_centered(draw, top + int(137 * scale), "Installable pets + an upstream-ready Ultra proposal", body, (187, 213, 241, int(240 * alpha)), width)
        else:
            title = font(FONT_BOLD, int(66 * scale))
            draw_centered(draw, top, "OPENAI — LET'S EVOLVE PETS.", title, (246, 249, 255, int(255 * alpha)), width, stroke=max(1, int(2 * scale)), stroke_fill=(3, 6, 14, 210))
            draw_centered(draw, top + int(83 * scale), "Installable pets + an upstream-ready Ultra proposal", body, (187, 213, 241, int(240 * alpha)), width)
        baseline = int((1005 if vertical else 670) * scale)
        pulse = 1.0 + 0.025 * math.sin(local * 5.0)
        if vertical:
            draw_sprite(image, "frostbyte", "waving", local, int(width * 0.28), baseline, 1.48 * scale * pulse, alpha)
            draw_sprite(image, "bolt", "waving", local + 0.2, int(width * 0.72), baseline, 1.48 * scale * pulse, alpha)
            link_y = int(1082 * scale)
        else:
            draw_sprite(image, "frostbyte", "waving", local, int(width * 0.34), baseline, 1.9 * scale * pulse, alpha)
            draw_sprite(image, "bolt", "waving", local + 0.2, int(width * 0.66), baseline, 1.9 * scale * pulse, alpha)
            link_y = int(670 * scale)
        draw_centered(draw, link_y, "github.com/Ashyboy219/codex-elemental-pets", mono, (255, 221, 74, int(250 * alpha)), width)

    for cut in (2.6, 6.0, 15.8):
        distance = abs(t - cut)
        if distance < 0.10:
            draw.rectangle((0, 0, width, height), fill=(220, 241, 255, int((1.0 - distance / 0.10) * 42)))
    rail_height = max(4, int(8 * scale))
    draw.rectangle((0, height - rail_height, width, height), fill=(22, 29, 51, 225))
    rail_time = 9.5 if 9.5 <= t < 13.2 else t
    draw.rectangle((0, height - rail_height, int(width * min(1.0, rail_time / DURATION)), height), fill=(255, 217, 63, 240))
    return image.convert("RGB")


def make_audio(path: Path) -> None:
    rate = 48_000
    samples = int(DURATION * rate)
    t = np.arange(samples, dtype=np.float64) / rate
    audio = np.zeros(samples, dtype=np.float64)
    for index, frequency in enumerate((92.5, 138.6, 185.0, 277.2)):
        audio += (0.019 / (index + 1) ** 0.3) * np.sin(2 * np.pi * frequency * t + index * 0.8)
    audio *= 0.70 + 0.30 * np.sin(2 * np.pi * 0.075 * t) ** 2
    for beat in np.arange(0, DURATION, 0.5):
        start = int(beat * rate)
        length = min(int(0.14 * rate), samples - start)
        local = np.arange(length) / rate
        audio[start : start + length] += 0.044 * np.sin(2 * np.pi * 76 * local) * np.exp(-local * 26)
    for cut, base in ((0.0, 660), (2.6, 780), (6.0, 990), (9.5, 1180), (13.2, 620), (15.8, 880)):
        start = int(cut * rate)
        length = min(int(0.72 * rate), samples - start)
        local = np.arange(length) / rate
        tone = np.sin(2 * np.pi * base * local) + 0.38 * np.sin(2 * np.pi * base * 1.5 * local)
        audio[start : start + length] += 0.06 * tone * np.exp(-local * 5.0)
    stereo = np.stack(
        (
            audio * (0.94 + 0.06 * np.sin(2 * np.pi * 0.12 * t)),
            audio * (0.94 + 0.06 * np.sin(2 * np.pi * 0.12 * t + math.pi)),
        ),
        axis=1,
    )
    stereo *= 0.72 / max(1e-9, float(np.abs(stereo).max()))
    pcm = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(pcm.tobytes())


def render_video(
    output: Path,
    source_size: tuple[int, int],
    target_size: tuple[int, int],
    vertical: bool,
    audio: Path,
    frost_ultra: Image.Image,
    bolt_ultra: Image.Image,
) -> None:
    width, height = source_size
    command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "rawvideo",
        "-pixel_format",
        "rgb24",
        "-video_size",
        f"{width}x{height}",
        "-framerate",
        str(FPS),
        "-i",
        "-",
        "-i",
        str(audio),
        "-vf",
        f"scale={target_size[0]}:{target_size[1]}:flags=lanczos",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "160k",
        "-shortest",
        "-movflags",
        "+faststart",
        str(output),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    assert process.stdin is not None
    total = int(DURATION * FPS)
    for index in range(total):
        frame = render_frame(width, height, index / FPS, vertical, frost_ultra, bolt_ultra)
        process.stdin.write(frame.tobytes())
        if index % (FPS * 3) == 0:
            print(f"{output.name}: {index}/{total}", flush=True)
    process.stdin.close()
    if process.wait():
        raise RuntimeError(f"ffmpeg failed while rendering {output}")


def main() -> None:
    MEDIA.mkdir(parents=True, exist_ok=True)
    DOCS_ASSETS.mkdir(parents=True, exist_ok=True)
    frost_ultra = load_ultra("frostbyte")
    bolt_ultra = load_ultra("bolt")
    audio = MEDIA / "evolution-soundtrack.wav"
    make_audio(audio)
    vertical = MEDIA / "evolution-showcase-vertical-1080x1920.mp4"
    landscape = MEDIA / "evolution-showcase-landscape-1920x1080.mp4"
    render_video(vertical, (720, 1280), (1080, 1920), True, audio, frost_ultra, bolt_ultra)
    render_video(landscape, (1280, 720), (1920, 1080), False, audio, frost_ultra, bolt_ultra)
    for item in (vertical, landscape):
        shutil.copy2(item, DOCS_ASSETS / item.name)
    print("evolution media build complete", flush=True)


if __name__ == "__main__":
    main()
