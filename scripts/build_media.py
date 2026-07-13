#!/usr/bin/env python3
"""Build social-native launch media from the validated Frostbyte and Bolt atlases."""

from __future__ import annotations

import math
import shutil
import subprocess
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / "media"
DOCS_ASSETS = ROOT / "docs" / "assets"
FPS = 24
DURATION = 15.0
CELL_W, CELL_H = 192, 208


def first_font(*candidates: str) -> Path:
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return path
    raise FileNotFoundError(f"No usable font found in: {', '.join(candidates)}")


FONT_BOLD = first_font(
    "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
)
FONT_REGULAR = first_font(
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)
FONT_MONO = first_font(
    "/System/Library/Fonts/SFNSMono.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
)

ROWS = {
    "idle": (0, 6),
    "running-right": (1, 8),
    "running-left": (2, 8),
    "waving": (3, 4),
    "jumping": (4, 5),
    "failed": (5, 8),
    "waiting": (6, 6),
    "running": (7, 6),
    "review": (8, 6),
    "look-up-to-down": (9, 8),
    "look-down-to-up": (10, 8),
}

ATLASES = {
    name: Image.open(ROOT / "pets" / name / "spritesheet.webp").convert("RGBA")
    for name in ("frostbyte", "bolt")
}


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size)


def smoothstep(value: float) -> float:
    value = min(1.0, max(0.0, value))
    return value * value * (3.0 - 2.0 * value)


def cell(pet: str, state: str, index: int) -> Image.Image:
    row, count = ROWS[state]
    index %= count
    return ATLASES[pet].crop(
        (index * CELL_W, row * CELL_H, (index + 1) * CELL_W, (row + 1) * CELL_H)
    )


def sprite_frame(pet: str, state: str, t: float, rate: float = 7.0) -> Image.Image:
    return cell(pet, state, int(t * rate))


def background(width: int, height: int) -> Image.Image:
    yy, xx = np.mgrid[0:height, 0:width]
    base = np.zeros((height, width, 3), dtype=np.float32)
    base[:] = (6, 9, 20)
    frost = np.exp(-(((xx - width * 0.20) / (width * 0.44)) ** 2 + ((yy - height * 0.58) / (height * 0.62)) ** 2))
    bolt = np.exp(-(((xx - width * 0.83) / (width * 0.42)) ** 2 + ((yy - height * 0.50) / (height * 0.58)) ** 2))
    top = np.clip(1.0 - yy / max(height, 1), 0, 1)
    base += frost[..., None] * np.array([6, 38, 57])
    base += bolt[..., None] * np.array([45, 26, 9])
    base += top[..., None] * np.array([5, 3, 13])
    base = np.clip(base, 0, 255).astype(np.uint8)
    image = Image.fromarray(base, "RGB").convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")
    grid = max(32, width // 24)
    for x in range(-height, width + height, grid):
        draw.line((x, 0, x - height, height), fill=(108, 133, 180, 10), width=1)
    for y in range(0, height, grid):
        draw.line((0, y, width, y), fill=(108, 133, 180, 8), width=1)
    return image


def add_particles(image: Image.Image, t: float) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    width, height = image.size
    rng = np.random.default_rng(90210)
    for i in range(24):
        x0 = float(rng.random()) * width * 0.54
        speed = 12 + float(rng.random()) * 26
        y = (float(rng.random()) * height + t * speed) % height
        x = x0 + math.sin(t * 0.8 + i) * 9
        size = 2 + (i % 3)
        alpha = 40 + (i % 5) * 13
        draw.rectangle((x, y, x + size, y + size), fill=(163, 235, 255, alpha))
    for i in range(16):
        x = width * 0.55 + ((i * 97 + t * (40 + i % 5)) % (width * 0.48))
        y = (i * 131 + t * (55 + i % 4)) % height
        length = 8 + (i % 4) * 3
        alpha = 45 + (i % 4) * 18
        draw.line((x, y, x + length * 0.45, y - length * 0.4), fill=(255, 221, 73, alpha), width=2)
        draw.line((x + length * 0.45, y - length * 0.4, x + length, y), fill=(255, 221, 73, alpha), width=2)


def draw_chip(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, scale: float) -> None:
    x, y = xy
    f = font(FONT_MONO, max(11, int(13 * scale)))
    bbox = draw.textbbox((0, 0), text, font=f)
    w = bbox[2] - bbox[0] + int(22 * scale)
    h = bbox[3] - bbox[1] + int(14 * scale)
    draw.rounded_rectangle((x, y, x + w, y + h), radius=int(9 * scale), fill=(13, 19, 38, 215), outline=(155, 177, 214, 65), width=max(1, int(scale)))
    draw.text((x + int(11 * scale), y + int(6 * scale)), text, font=f, fill=(208, 218, 239, 225))


def draw_centered(draw: ImageDraw.ImageDraw, y: int, text: str, f: ImageFont.FreeTypeFont, fill, width: int, stroke: int = 0, stroke_fill=(0, 0, 0, 0)) -> None:
    bbox = draw.textbbox((0, 0), text, font=f, stroke_width=stroke)
    x = (width - (bbox[2] - bbox[0])) // 2
    draw.text((x, y), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)


def draw_sprite(image: Image.Image, pet: str, state: str, t: float, center_x: int, baseline_y: int, scale: float, opacity: float = 1.0, rate: float = 7.0) -> None:
    sprite = sprite_frame(pet, state, t, rate=rate)
    target = sprite.resize((max(1, int(CELL_W * scale)), max(1, int(CELL_H * scale))), Image.Resampling.NEAREST)
    if opacity < 0.999:
        alpha = target.getchannel("A").point(lambda value: int(value * opacity))
        target.putalpha(alpha)
    image.alpha_composite(target, (int(center_x - target.width / 2), int(baseline_y - target.height)))


def scene_fade(t: float, start: float, end: float, edge: float = 0.25) -> float:
    return smoothstep((t - start) / edge) * smoothstep((end - t) / edge)


def render_frame(width: int, height: int, t: float, vertical: bool) -> Image.Image:
    image = background(width, height)
    add_particles(image, t)
    draw = ImageDraw.Draw(image, "RGBA")
    scale = width / (720 if vertical else 1280)
    safe = int(34 * scale)
    draw_chip(draw, (safe, safe), "UNOFFICIAL COMMUNITY PETS", scale)

    # Scene 1 — instant two-character hook.
    if t < 2.7:
        alpha = scene_fade(t, 0.0, 2.7, 0.20)
        title_size = int((62 if vertical else 58) * scale)
        sub_size = int((27 if vertical else 24) * scale)
        title = font(FONT_BOLD, title_size)
        sub = font(FONT_REGULAR, sub_size)
        y = int((128 if vertical else 70) * scale)
        draw_centered(draw, y, "CODEX JUST GOT", title, (244, 248, 255, int(255 * alpha)), width, stroke=max(1, int(2 * scale)), stroke_fill=(3, 6, 15, 180))
        draw_centered(draw, y + int(67 * scale), "TWO NEW ELEMENTS", title, (255, 218, 77, int(255 * alpha)), width, stroke=max(1, int(2 * scale)), stroke_fill=(3, 6, 15, 180))
        draw_centered(draw, y + int(145 * scale), "Frostbyte  ×  Bolt", sub, (176, 218, 244, int(235 * alpha)), width)
        if vertical:
            baseline = int(1015 * scale)
            pulse = 1.0 + 0.035 * math.sin(t * 5)
            draw_sprite(image, "frostbyte", "jumping", t, int(width * 0.27), baseline, 1.60 * scale * pulse, alpha)
            draw_sprite(image, "bolt", "jumping", t + 0.22, int(width * 0.73), baseline, 1.60 * scale * pulse, alpha)
        else:
            baseline = int(650 * scale)
            draw_sprite(image, "frostbyte", "jumping", t, int(width * 0.34), baseline, 1.88 * scale, alpha)
            draw_sprite(image, "bolt", "jumping", t + 0.22, int(width * 0.66), baseline, 1.88 * scale, alpha)

    # Scene 2 — Frostbyte personality.
    elif t < 5.7:
        local = t - 2.7
        alpha = scene_fade(t, 2.7, 5.7)
        title = font(FONT_BOLD, int((74 if vertical else 72) * scale))
        kicker = font(FONT_MONO, int(18 * scale))
        body = font(FONT_REGULAR, int((26 if vertical else 25) * scale))
        if vertical:
            draw_centered(draw, int(148 * scale), "FROSTBYTE", title, (203, 244, 255, int(255 * alpha)), width, stroke=max(1, int(2 * scale)), stroke_fill=(4, 17, 34, 190))
            draw_centered(draw, int(238 * scale), "ICE / PRECISION", kicker, (99, 207, 243, int(230 * alpha)), width)
            draw_centered(draw, int(1035 * scale), "Cool-headed. Patient. Exact.", body, (226, 237, 250, int(240 * alpha)), width)
            state = "waving" if local < 1.5 else "review"
            draw_sprite(image, "frostbyte", state, local, width // 2, int(980 * scale), 2.65 * scale, alpha)
        else:
            draw.text((int(95 * scale), int(150 * scale)), "FROSTBYTE", font=title, fill=(203, 244, 255, int(255 * alpha)), stroke_width=max(1, int(2 * scale)), stroke_fill=(4, 17, 34, 190))
            draw.text((int(99 * scale), int(238 * scale)), "ICE / PRECISION", font=kicker, fill=(99, 207, 243, int(230 * alpha)))
            draw.text((int(99 * scale), int(292 * scale)), "Cool-headed.\nPatient. Exact.", font=body, fill=(226, 237, 250, int(240 * alpha)), spacing=int(10 * scale))
            state = "waving" if local < 1.5 else "review"
            draw_sprite(image, "frostbyte", state, local, int(width * 0.72), int(670 * scale), 2.55 * scale, alpha)

    # Scene 3 — Bolt personality.
    elif t < 8.7:
        local = t - 5.7
        alpha = scene_fade(t, 5.7, 8.7)
        title = font(FONT_BOLD, int((82 if vertical else 80) * scale))
        kicker = font(FONT_MONO, int(18 * scale))
        body = font(FONT_REGULAR, int((26 if vertical else 25) * scale))
        if vertical:
            draw_centered(draw, int(148 * scale), "BOLT", title, (255, 223, 70, int(255 * alpha)), width, stroke=max(1, int(2 * scale)), stroke_fill=(24, 8, 34, 190))
            draw_centered(draw, int(246 * scale), "LIGHTNING / MOMENTUM", kicker, (199, 154, 255, int(230 * alpha)), width)
            draw_centered(draw, int(1035 * scale), "Restless. Brave. Ready.", body, (240, 232, 251, int(240 * alpha)), width)
            state = "jumping" if local < 1.35 else "waving"
            draw_sprite(image, "bolt", state, local, width // 2, int(980 * scale), 2.65 * scale, alpha)
        else:
            draw.text((int(770 * scale), int(150 * scale)), "BOLT", font=title, fill=(255, 223, 70, int(255 * alpha)), stroke_width=max(1, int(2 * scale)), stroke_fill=(24, 8, 34, 190))
            draw.text((int(773 * scale), int(244 * scale)), "LIGHTNING / MOMENTUM", font=kicker, fill=(199, 154, 255, int(230 * alpha)))
            draw.text((int(773 * scale), int(298 * scale)), "Restless.\nBrave. Ready.", font=body, fill=(240, 232, 251, int(240 * alpha)), spacing=int(10 * scale))
            state = "jumping" if local < 1.35 else "waving"
            draw_sprite(image, "bolt", state, local, int(width * 0.32), int(670 * scale), 2.55 * scale, alpha)

    # Scene 4 — quality proof.
    elif t < 12.0:
        local = t - 8.7
        alpha = scene_fade(t, 8.7, 12.0)
        big = font(FONT_BOLD, int((40 if vertical else 54) * scale))
        stat = font(FONT_MONO, int((22 if vertical else 20) * scale))
        y = int((132 if vertical else 58) * scale)
        draw_centered(draw, y, "PERSONALITY IN EVERY POSE", big, (246, 248, 255, int(255 * alpha)), width, stroke=max(1, int(2 * scale)), stroke_fill=(5, 7, 18, 190))
        draw_centered(draw, y + int(80 * scale), "11 ANIMATION ROWS  •  16 LOOK DIRECTIONS", stat, (171, 199, 236, int(235 * alpha)), width)
        state = "look-up-to-down" if local < 1.65 else "look-down-to-up"
        if vertical:
            draw_sprite(image, "frostbyte", state, local, int(width * 0.27), int(955 * scale), 1.60 * scale, alpha, rate=4.7)
            draw_sprite(image, "bolt", state, local + 0.1, int(width * 0.73), int(955 * scale), 1.60 * scale, alpha, rate=4.7)
        else:
            draw_sprite(image, "frostbyte", state, local, int(width * 0.35), int(665 * scale), 2.05 * scale, alpha, rate=4.7)
            draw_sprite(image, "bolt", state, local + 0.1, int(width * 0.65), int(665 * scale), 2.05 * scale, alpha, rate=4.7)

    # Scene 5 — CTA.
    else:
        local = t - 12.0
        alpha = scene_fade(t, 12.0, 15.0, 0.25)
        title = font(FONT_BOLD, int((38 if vertical else 62) * scale))
        body = font(FONT_REGULAR, int((25 if vertical else 24) * scale))
        mono = font(FONT_MONO, int((17 if vertical else 18) * scale))
        y = int((122 if vertical else 55) * scale)
        draw_centered(draw, y, "OPEN-SOURCE. READY TO HATCH.", title, (247, 249, 255, int(255 * alpha)), width, stroke=max(1, int(2 * scale)), stroke_fill=(4, 6, 15, 200))
        draw_centered(draw, y + int(90 * scale), "Two fully animated v2 pets for Codex", body, (188, 211, 240, int(235 * alpha)), width)
        baseline = int((982 if vertical else 645) * scale)
        if vertical:
            draw_sprite(image, "frostbyte", "waving", local, int(width * 0.28), baseline, 1.62 * scale, alpha)
            draw_sprite(image, "bolt", "waving", local + 0.3, int(width * 0.72), baseline, 1.62 * scale, alpha)
            link_y = int(1080 * scale)
        else:
            draw_sprite(image, "frostbyte", "waving", local, int(width * 0.35), baseline, 1.95 * scale, alpha)
            draw_sprite(image, "bolt", "waving", local + 0.3, int(width * 0.65), baseline, 1.95 * scale, alpha)
            link_y = int(655 * scale)
        draw_centered(draw, link_y, "github.com/Ashyboy219/codex-elemental-pets", mono, (255, 223, 70, int(250 * alpha)), width)

    # Transition flashes and a minimal progress rail.
    for cut in (2.7, 5.7, 8.7, 12.0):
        distance = abs(t - cut)
        if distance < 0.10:
            flash = int((1.0 - distance / 0.10) * 35)
            draw.rectangle((0, 0, width, height), fill=(214, 237, 255, flash))
    rail_y = height - max(4, int(8 * scale))
    draw.rectangle((0, rail_y, width, height), fill=(24, 31, 54, 220))
    progress = int(width * min(1.0, t / DURATION))
    draw.rectangle((0, rail_y, progress, height), fill=(255, 215, 61, 235))
    return image.convert("RGB")


def make_audio(path: Path) -> None:
    rate = 48_000
    n = int(DURATION * rate)
    t = np.arange(n, dtype=np.float64) / rate
    audio = np.zeros(n, dtype=np.float64)

    # Low, original synth bed.
    chord = (110.0, 164.81, 220.0, 329.63)
    for i, frequency in enumerate(chord):
        audio += (0.020 / (i + 1) ** 0.25) * np.sin(2 * np.pi * frequency * t + i * 0.7)
    audio *= 0.72 + 0.28 * np.sin(2 * np.pi * 0.08 * t) ** 2

    # Soft pulse and scene-change chimes.
    for beat in np.arange(0, DURATION, 0.5):
        start = int(beat * rate)
        length = min(int(0.16 * rate), n - start)
        local = np.arange(length) / rate
        audio[start:start + length] += 0.045 * np.sin(2 * np.pi * 72 * local) * np.exp(-local * 24)
    for cut, base in ((0.0, 660), (2.7, 880), (5.7, 520), (8.7, 740), (12.0, 990)):
        start = int(cut * rate)
        length = min(int(0.65 * rate), n - start)
        local = np.arange(length) / rate
        tone = (np.sin(2 * np.pi * base * local) + 0.45 * np.sin(2 * np.pi * base * 1.5 * local))
        audio[start:start + length] += 0.055 * tone * np.exp(-local * 4.8)

    # Quiet stereo motion to keep the mix alive without overpowering captions.
    left = audio * (0.94 + 0.06 * np.sin(2 * np.pi * 0.13 * t))
    right = audio * (0.94 + 0.06 * np.sin(2 * np.pi * 0.13 * t + math.pi))
    stereo = np.stack((left, right), axis=1)
    peak = max(1e-9, float(np.abs(stereo).max()))
    stereo = np.clip(stereo * (0.72 / peak), -1, 1)
    pcm = (stereo * 32767).astype("<i2")
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(pcm.tobytes())


def render_video(name: str, source_size: tuple[int, int], target_size: tuple[int, int], vertical: bool, audio: Path) -> Path:
    output = MEDIA / name
    if output.exists() and output.stat().st_size > 0:
        print(f"{name}: reusing existing render", flush=True)
        return output
    width, height = source_size
    command = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", f"{width}x{height}",
        "-framerate", str(FPS), "-i", "-", "-i", str(audio),
        "-vf", f"scale={target_size[0]}:{target_size[1]}:flags=lanczos",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(output),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    assert process.stdin is not None
    total = int(DURATION * FPS)
    for index in range(total):
        frame = render_frame(width, height, index / FPS, vertical=vertical)
        process.stdin.write(frame.tobytes())
        if index % (FPS * 3) == 0:
            print(f"{name}: {index}/{total}", flush=True)
    process.stdin.close()
    return_code = process.wait()
    if return_code:
        raise RuntimeError(f"ffmpeg failed for {name} with status {return_code}")
    return output


def poster(path: Path, width: int, height: int, vertical: bool) -> None:
    if path.exists() and path.stat().st_size > 0:
        return
    image = background(width, height)
    add_particles(image, 2.0)
    draw = ImageDraw.Draw(image, "RGBA")
    scale = width / (1080 if vertical else 1200)
    draw_chip(draw, (int(54 * scale), int(50 * scale)), "UNOFFICIAL COMMUNITY PETS", scale * 1.2)
    title = font(FONT_BOLD, int((88 if vertical else 84) * scale))
    subtitle = font(FONT_REGULAR, int((35 if vertical else 31) * scale))
    mono = font(FONT_MONO, int((22 if vertical else 19) * scale))
    draw_centered(draw, int((190 if vertical else 90) * scale), "FROSTBYTE  ×  BOLT", title, (247, 250, 255, 255), width, stroke=max(2, int(3 * scale)), stroke_fill=(4, 7, 18, 210))
    draw_centered(draw, int((305 if vertical else 195) * scale), "Two new elemental pets for Codex", subtitle, (192, 214, 242, 245), width)
    if vertical:
        draw_sprite(image, "frostbyte", "waving", 0.25, int(width * 0.28), int(height * 0.76), 2.15 * scale)
        draw_sprite(image, "bolt", "waving", 0.55, int(width * 0.72), int(height * 0.76), 2.15 * scale)
        stat_y = int(height * 0.79)
        link_y = int(height * 0.88)
    else:
        draw_sprite(image, "frostbyte", "waving", 0.25, int(width * 0.35), int(height * 0.90), 2.00 * scale)
        draw_sprite(image, "bolt", "waving", 0.55, int(width * 0.65), int(height * 0.90), 2.00 * scale)
        stat_y = int(height * 0.79)
        link_y = int(height * 0.91)
    draw_centered(draw, stat_y, "11 ANIMATION ROWS  •  16 LOOK DIRECTIONS  •  V2", mono, (255, 220, 72, 245), width)
    draw_centered(draw, link_y, "github.com/Ashyboy219/codex-elemental-pets", mono, (194, 212, 238, 235), width)
    image.convert("RGB").save(path, quality=96)


def build_loops(landscape_video: Path) -> None:
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(landscape_video), "-t", "12",
        "-vf", "fps=10,scale=720:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer:bayer_scale=4",
        "-loop", "0", str(MEDIA / "showcase-loop.gif"),
    ], check=True)


def main() -> None:
    MEDIA.mkdir(parents=True, exist_ok=True)
    DOCS_ASSETS.mkdir(parents=True, exist_ok=True)
    audio = MEDIA / "original-soundtrack.wav"
    make_audio(audio)
    vertical_video = render_video("showcase-vertical-1080x1920.mp4", (720, 1280), (1080, 1920), True, audio)
    landscape_video = render_video("showcase-landscape-1920x1080.mp4", (1280, 720), (1920, 1080), False, audio)
    poster(MEDIA / "poster-square-1080x1080.png", 1080, 1080, True)
    poster(MEDIA / "poster-landscape-1200x675.png", 1200, 675, False)
    poster(MEDIA / "poster-vertical-1080x1920.png", 1080, 1920, True)
    build_loops(landscape_video)
    for item in (
        vertical_video,
        landscape_video,
        MEDIA / "poster-square-1080x1080.png",
        MEDIA / "poster-landscape-1200x675.png",
        MEDIA / "showcase-loop.gif",
        MEDIA / "frostbyte-waving.gif",
        MEDIA / "bolt-waving.gif",
    ):
        shutil.copy2(item, DOCS_ASSETS / item.name)
    print("media build complete", flush=True)


if __name__ == "__main__":
    main()
