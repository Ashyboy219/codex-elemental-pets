#!/usr/bin/env python3
"""Build social-native launch media from the four validated Codex pet atlases."""

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
PETS = ("frostbyte", "bolt", "cinder", "mantra")
SCENE_CUTS = (2.5, 5.0, 7.5, 11.5)

PET_META = {
    "frostbyte": {
        "name": "FROSTBYTE",
        "power": "ICE / PRECISION",
        "line": "Cool-headed. Patient. Exact.",
        "accent": (126, 225, 255),
        "secondary": (65, 143, 232),
    },
    "bolt": {
        "name": "BOLT",
        "power": "LIGHTNING / MOMENTUM",
        "line": "Restless. Brave. Ready.",
        "accent": (255, 222, 65),
        "secondary": (183, 120, 255),
    },
    "cinder": {
        "name": "CINDER",
        "power": "SMOKE + ASH / RESILIENCE",
        "line": "Wry. Tenacious. Rebuilds.",
        "accent": (255, 129, 74),
        "secondary": (164, 177, 194),
    },
    "mantra": {
        "name": "MANTRA",
        "power": "MIND / CLARITY",
        "line": "Still. Perceptive. Threefold.",
        "accent": (189, 140, 255),
        "secondary": (84, 231, 222),
    },
}


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

ATLASES: dict[str, Image.Image] = {}


def atlas(pet: str) -> Image.Image:
    """Load an atlas on demand so Frostbyte/Bolt-only tools remain importable."""
    if pet not in PETS:
        raise KeyError(f"Unknown pet: {pet}")
    if pet not in ATLASES:
        path = ROOT / "pets" / pet / "spritesheet.webp"
        if not path.exists():
            raise FileNotFoundError(
                f"Missing validated atlas for {pet}: {path}. "
                "Land all four pet binaries before running this media build."
            )
        loaded = Image.open(path).convert("RGBA")
        expected = (CELL_W * 8, CELL_H * 11)
        if loaded.size != expected:
            raise ValueError(
                f"{pet} atlas is {loaded.size}; expected v2 atlas {expected}"
            )
        ATLASES[pet] = loaded
    return ATLASES[pet]


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size)


def smoothstep(value: float) -> float:
    value = min(1.0, max(0.0, value))
    return value * value * (3.0 - 2.0 * value)


def cell(pet: str, state: str, index: int) -> Image.Image:
    row, count = ROWS[state]
    index %= count
    return atlas(pet).crop(
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


def collection_background(width: int, height: int) -> Image.Image:
    """Four-corner color field for the complete collection."""
    yy, xx = np.mgrid[0:height, 0:width]
    base = np.zeros((height, width, 3), dtype=np.float32)
    base[:] = (5, 7, 17)
    fields = (
        (0.17, 0.25, (7, 46, 70)),
        (0.82, 0.24, (53, 28, 8)),
        (0.18, 0.82, (52, 22, 17)),
        (0.82, 0.80, (38, 20, 67)),
    )
    for x_ratio, y_ratio, color in fields:
        distance = (
            ((xx - width * x_ratio) / (width * 0.39)) ** 2
            + ((yy - height * y_ratio) / (height * 0.42)) ** 2
        )
        base += np.exp(-distance)[..., None] * np.array(color)
    top = np.clip(1.0 - yy / max(height, 1), 0, 1)
    base += top[..., None] * np.array([5, 3, 12])
    image = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB").convert(
        "RGBA"
    )
    draw = ImageDraw.Draw(image, "RGBA")
    grid = max(30, width // 24)
    for x in range(-height, width + height, grid):
        draw.line((x, 0, x - height, height), fill=(129, 143, 190, 9), width=1)
    for y in range(0, height, grid):
        draw.line((0, y, width, y), fill=(129, 143, 190, 7), width=1)
    return image


def add_collection_particles(image: Image.Image, t: float) -> None:
    """Deterministic atmosphere with one restrained motif per power."""
    draw = ImageDraw.Draw(image, "RGBA")
    width, height = image.size
    rng = np.random.default_rng(40704)

    # Frostbyte: crisp drifting ice pixels.
    for i in range(15):
        x = (float(rng.random()) * width * 0.44 + math.sin(t + i) * 5) % width
        y = (float(rng.random()) * height + t * (11 + i % 5)) % height
        size = 2 + i % 3
        draw.rectangle((x, y, x + size, y + size), fill=(168, 237, 255, 48))

    # Bolt: compact angular sparks.
    for i in range(11):
        x = width * 0.55 + ((i * 89 + t * (32 + i % 4)) % (width * 0.44))
        y = (i * 103 + t * (41 + i % 3)) % (height * 0.58)
        length = 7 + i % 4 * 2
        draw.line(
            (x, y, x + length * 0.45, y - length * 0.42),
            fill=(255, 223, 77, 55),
            width=2,
        )
        draw.line(
            (x + length * 0.45, y - length * 0.42, x + length, y),
            fill=(255, 223, 77, 55),
            width=2,
        )

    # Cinder: slow ash motes, kept in the background rather than on the sprite.
    for i in range(13):
        x = (i * 71 + t * (9 + i % 5)) % (width * 0.48)
        y = height * 0.53 + ((i * 67 - t * (13 + i % 3)) % (height * 0.46))
        radius = 1 + i % 3
        draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            fill=(207, 136, 106, 42 + i % 4 * 7),
        )

    # Mantra: measured orbit points suggesting focus and inward motion.
    center_x, center_y = width * 0.80, height * 0.79
    orbit = min(width, height) * 0.12
    for i in range(9):
        angle = t * 0.16 + i * math.tau / 9
        x = center_x + math.cos(angle) * orbit
        y = center_y + math.sin(angle) * orbit * 0.46
        radius = 1 + i % 2
        draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            fill=(158, 137, 255, 34 + i % 3 * 8),
        )


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


def draw_pet_tag(
    draw: ImageDraw.ImageDraw,
    center_x: int,
    y: int,
    pet: str,
    scale: float,
    opacity: float = 1.0,
) -> None:
    meta = PET_META[pet]
    label_font = font(FONT_MONO, max(10, int(14 * scale)))
    label = meta["name"]
    bbox = draw.textbbox((0, 0), label, font=label_font)
    pad_x, pad_y = int(10 * scale), int(5 * scale)
    width = bbox[2] - bbox[0] + pad_x * 2
    height = bbox[3] - bbox[1] + pad_y * 2
    x = int(center_x - width / 2)
    accent = meta["accent"]
    draw.rounded_rectangle(
        (x, y, x + width, y + height),
        radius=max(4, int(8 * scale)),
        fill=(9, 13, 27, int(220 * opacity)),
        outline=(*accent, int(150 * opacity)),
        width=max(1, int(scale)),
    )
    draw.text(
        (x + pad_x, y + pad_y),
        label,
        font=label_font,
        fill=(*accent, int(245 * opacity)),
    )


def draw_power_field(
    image: Image.Image,
    pet: str,
    center_x: int,
    center_y: int,
    radius: int,
    opacity: float,
) -> None:
    """Add scene-level palette identity without altering or redrawing pet art."""
    draw = ImageDraw.Draw(image, "RGBA")
    accent = PET_META[pet]["accent"]
    secondary = PET_META[pet]["secondary"]
    for step in range(4, 0, -1):
        inset = int(radius * (4 - step) * 0.17)
        alpha = int((13 + step * 6) * opacity)
        draw.ellipse(
            (
                center_x - radius + inset,
                center_y - radius + inset,
                center_x + radius - inset,
                center_y + radius - inset,
            ),
            outline=(*accent, alpha),
            width=max(1, step),
        )
    inner = int(radius * 0.58)
    draw.ellipse(
        (center_x - inner, center_y - inner, center_x + inner, center_y + inner),
        fill=(*secondary, int(13 * opacity)),
    )


def render_frame(width: int, height: int, t: float, vertical: bool) -> Image.Image:
    image = collection_background(width, height)
    add_collection_particles(image, t)
    draw = ImageDraw.Draw(image, "RGBA")
    scale = width / (720 if vertical else 1280)
    safe = int(34 * scale)
    draw_chip(draw, (safe, safe), "UNOFFICIAL COMMUNITY PETS", scale)

    # Scene 1 — poster-like four-character hook in the opening frame.
    if t < 2.5:
        alpha = scene_fade(t, 0.0, 2.5, 0.18)
        title_size = int((56 if vertical else 57) * scale)
        sub_size = int((23 if vertical else 22) * scale)
        title = font(FONT_BOLD, title_size)
        sub = font(FONT_REGULAR, sub_size)
        y = int((122 if vertical else 68) * scale)
        draw_centered(
            draw,
            y,
            "FOUR POWERS.",
            title,
            (244, 248, 255, int(255 * alpha)),
            width,
            stroke=max(1, int(2 * scale)),
            stroke_fill=(3, 6, 15, 180),
        )
        draw_centered(
            draw,
            y + int(66 * scale),
            "ONE CODEX CREW.",
            title,
            (255, 218, 77, int(255 * alpha)),
            width,
            stroke=max(1, int(2 * scale)),
            stroke_fill=(3, 6, 15, 180),
        )
        draw_centered(
            draw,
            y + int(143 * scale),
            "Frostbyte  •  Bolt  •  Cinder  •  Mantra",
            sub,
            (189, 211, 242, int(235 * alpha)),
            width,
        )
        if vertical:
            positions = (
                ("frostbyte", 0.27, 660, "waving", 0.00),
                ("bolt", 0.73, 660, "jumping", 0.18),
                ("cinder", 0.27, 1090, "running", 0.31),
                ("mantra", 0.73, 1090, "idle", 0.47),
            )
            sprite_scale = 1.38 * scale
        else:
            positions = tuple(
                (pet, x, 650, state, offset)
                for pet, x, state, offset in (
                    ("frostbyte", 0.14, "waving", 0.00),
                    ("bolt", 0.38, "jumping", 0.18),
                    ("cinder", 0.62, "running", 0.31),
                    ("mantra", 0.86, "idle", 0.47),
                )
            )
            sprite_scale = 1.35 * scale
        for pet, x_ratio, baseline, state, offset in positions:
            draw_sprite(
                image,
                pet,
                state,
                t + offset,
                int(width * x_ratio),
                int(baseline * scale),
                sprite_scale,
                alpha,
            )

    # Scene 2 — Cinder gets a smoky, ember-toned personality beat.
    elif t < 5.0:
        local = t - 2.5
        alpha = scene_fade(t, 2.5, 5.0)
        title = font(FONT_BOLD, int((78 if vertical else 76) * scale))
        kicker = font(FONT_MONO, int(18 * scale))
        body = font(FONT_REGULAR, int((26 if vertical else 25) * scale))
        meta = PET_META["cinder"]
        if vertical:
            draw_power_field(image, "cinder", width // 2, int(675 * scale), int(300 * scale), alpha)
            draw_centered(draw, int(148 * scale), meta["name"], title, (*meta["accent"], int(255 * alpha)), width, stroke=max(1, int(2 * scale)), stroke_fill=(31, 8, 5, 190))
            draw_centered(draw, int(242 * scale), meta["power"], kicker, (*meta["secondary"], int(235 * alpha)), width)
            draw_centered(draw, int(1050 * scale), meta["line"], body, (241, 225, 220, int(240 * alpha)), width)
            state = "running" if local < 1.25 else "review"
            draw_sprite(image, "cinder", state, local, width // 2, int(985 * scale), 2.55 * scale, alpha)
        else:
            draw_power_field(image, "cinder", int(width * 0.72), int(400 * scale), int(260 * scale), alpha)
            draw.text((int(92 * scale), int(150 * scale)), meta["name"], font=title, fill=(*meta["accent"], int(255 * alpha)), stroke_width=max(1, int(2 * scale)), stroke_fill=(31, 8, 5, 190))
            draw.text((int(96 * scale), int(242 * scale)), meta["power"], font=kicker, fill=(*meta["secondary"], int(235 * alpha)))
            draw.text((int(96 * scale), int(296 * scale)), "Wry. Tenacious.\nAlways rebuilds.", font=body, fill=(241, 225, 220, int(240 * alpha)), spacing=int(10 * scale))
            state = "running" if local < 1.25 else "review"
            draw_sprite(image, "cinder", state, local, int(width * 0.72), int(670 * scale), 2.52 * scale, alpha)

    # Scene 3 — Mantra gets a quiet, centered, threefold mind beat.
    elif t < 7.5:
        local = t - 5.0
        alpha = scene_fade(t, 5.0, 7.5)
        title = font(FONT_BOLD, int((82 if vertical else 80) * scale))
        kicker = font(FONT_MONO, int(18 * scale))
        body = font(FONT_REGULAR, int((26 if vertical else 25) * scale))
        meta = PET_META["mantra"]
        if vertical:
            draw_power_field(image, "mantra", width // 2, int(650 * scale), int(315 * scale), alpha)
            draw_centered(draw, int(148 * scale), meta["name"], title, (*meta["accent"], int(255 * alpha)), width, stroke=max(1, int(2 * scale)), stroke_fill=(13, 7, 37, 190))
            draw_centered(draw, int(246 * scale), meta["power"], kicker, (*meta["secondary"], int(235 * alpha)), width)
            draw_centered(draw, int(1050 * scale), meta["line"], body, (232, 228, 251, int(240 * alpha)), width)
            state = "idle" if local < 1.25 else "review"
            draw_sprite(image, "mantra", state, local, width // 2, int(985 * scale), 2.55 * scale, alpha, rate=4.5)
        else:
            draw_power_field(image, "mantra", int(width * 0.30), int(400 * scale), int(270 * scale), alpha)
            draw.text((int(762 * scale), int(150 * scale)), meta["name"], font=title, fill=(*meta["accent"], int(255 * alpha)), stroke_width=max(1, int(2 * scale)), stroke_fill=(13, 7, 37, 190))
            draw.text((int(766 * scale), int(246 * scale)), meta["power"], font=kicker, fill=(*meta["secondary"], int(235 * alpha)))
            draw.text((int(766 * scale), int(300 * scale)), "Still. Perceptive.\nThreefold focus.", font=body, fill=(232, 228, 251, int(240 * alpha)), spacing=int(10 * scale))
            state = "idle" if local < 1.25 else "review"
            draw_sprite(image, "mantra", state, local, int(width * 0.30), int(670 * scale), 2.52 * scale, alpha, rate=4.5)

    # Scene 4 — all four prove the shared v2 direction system.
    elif t < 11.5:
        local = t - 7.5
        alpha = scene_fade(t, 7.5, 11.5)
        big = font(FONT_BOLD, int((38 if vertical else 50) * scale))
        stat = font(FONT_MONO, int((19 if vertical else 19) * scale))
        y = int((132 if vertical else 58) * scale)
        draw_centered(draw, y, "PERSONALITY IN EVERY POSE", big, (246, 248, 255, int(255 * alpha)), width, stroke=max(1, int(2 * scale)), stroke_fill=(5, 7, 18, 190))
        draw_centered(draw, y + int(75 * scale), "4 PETS  •  11 ROWS EACH  •  16 LOOK DIRECTIONS", stat, (171, 199, 236, int(235 * alpha)), width)
        state = "look-up-to-down" if local < 2.0 else "look-down-to-up"
        if vertical:
            positions = (
                ("frostbyte", 0.27, 650, 0.00),
                ("bolt", 0.73, 650, 0.11),
                ("cinder", 0.27, 1080, 0.22),
                ("mantra", 0.73, 1080, 0.33),
            )
            sprite_scale = 1.38 * scale
            tag_offset = int(18 * scale)
        else:
            positions = (
                ("frostbyte", 0.14, 642, 0.00),
                ("bolt", 0.38, 642, 0.11),
                ("cinder", 0.62, 642, 0.22),
                ("mantra", 0.86, 642, 0.33),
            )
            sprite_scale = 1.34 * scale
            tag_offset = int(14 * scale)
        for pet, x_ratio, baseline, offset in positions:
            center_x = int(width * x_ratio)
            baseline_y = int(baseline * scale)
            draw_sprite(image, pet, state, local + offset, center_x, baseline_y, sprite_scale, alpha, rate=4.7)
            draw_pet_tag(draw, center_x, baseline_y + tag_offset, pet, scale, alpha)

    # Scene 5 — CTA.
    else:
        local = t - 11.5
        alpha = scene_fade(t, 11.5, 15.0, 0.25)
        title = font(FONT_BOLD, int((36 if vertical else 58) * scale))
        body = font(FONT_REGULAR, int((23 if vertical else 23) * scale))
        mono = font(FONT_MONO, int((15 if vertical else 17) * scale))
        y = int((122 if vertical else 55) * scale)
        draw_centered(draw, y, "OPEN-SOURCE. READY TO HATCH.", title, (247, 249, 255, int(255 * alpha)), width, stroke=max(1, int(2 * scale)), stroke_fill=(4, 6, 15, 200))
        draw_centered(draw, y + int(82 * scale), "Four fully animated v2 pets for Codex", body, (188, 211, 240, int(235 * alpha)), width)
        if vertical:
            positions = (
                ("frostbyte", 0.27, 650, 0.00),
                ("bolt", 0.73, 650, 0.18),
                ("cinder", 0.27, 1075, 0.36),
                ("mantra", 0.73, 1075, 0.54),
            )
            sprite_scale = 1.36 * scale
            link_y = int(1190 * scale)
        else:
            positions = (
                ("frostbyte", 0.14, 625, 0.00),
                ("bolt", 0.38, 625, 0.18),
                ("cinder", 0.62, 625, 0.36),
                ("mantra", 0.86, 625, 0.54),
            )
            sprite_scale = 1.32 * scale
            link_y = int(655 * scale)
        for pet, x_ratio, baseline, offset in positions:
            draw_sprite(image, pet, "waving", local + offset, int(width * x_ratio), int(baseline * scale), sprite_scale, alpha)
        draw_centered(draw, link_y, "github.com/Ashyboy219/codex-elemental-pets", mono, (255, 223, 70, int(250 * alpha)), width)

    # Transition flashes and a minimal progress rail.
    for cut in SCENE_CUTS:
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

    # Soft pulse and deterministic scene-change chimes.
    for beat in np.arange(0, DURATION, 0.5):
        start = int(beat * rate)
        length = min(int(0.16 * rate), n - start)
        local = np.arange(length) / rate
        audio[start:start + length] += 0.045 * np.sin(2 * np.pi * 72 * local) * np.exp(-local * 24)
    for cut, base in (
        (0.0, 660),
        (SCENE_CUTS[0], 440),  # Cinder: low ember tone.
        (SCENE_CUTS[1], 783),  # Mantra: clear upper tone.
        (SCENE_CUTS[2], 740),
        (SCENE_CUTS[3], 990),
    ):
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
    width, height = source_size
    command = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", f"{width}x{height}",
        "-framerate", str(FPS), "-i", "-", "-i", str(audio),
        # Source sizes are exact half-resolution; nearest preserves sprite pixels.
        "-vf", f"scale={target_size[0]}:{target_size[1]}:flags=neighbor",
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
    image = collection_background(width, height)
    add_collection_particles(image, 2.0)
    draw = ImageDraw.Draw(image, "RGBA")
    orientation = (
        "portrait"
        if height / width > 1.35
        else "square"
        if height / width > 0.82
        else "landscape"
    )
    scale = width / (1080 if orientation != "landscape" else 1200)
    draw_chip(draw, (int(54 * scale), int(50 * scale)), "UNOFFICIAL COMMUNITY PETS", scale * 1.2)
    if orientation == "portrait":
        title_size, subtitle_size, mono_size = 84, 31, 19
        title_y, subtitle_y = 175, 370
        positions = (
            ("frostbyte", 0.28, 920, "waving", 0.25),
            ("bolt", 0.72, 920, "waving", 0.55),
            ("cinder", 0.28, 1440, "running", 0.75),
            ("mantra", 0.72, 1440, "idle", 0.95),
        )
        sprite_scale = 2.0 * scale
        field_radius = int(190 * scale)
        stat_y = int(height * 0.85)
        link_y = int(height * 0.92)
    elif orientation == "square":
        title_size, subtitle_size, mono_size = 70, 28, 17
        title_y, subtitle_y = 130, 315
        positions = (
            ("frostbyte", 0.13, 835, "waving", 0.25),
            ("bolt", 0.38, 835, "waving", 0.55),
            ("cinder", 0.62, 835, "running", 0.75),
            ("mantra", 0.87, 835, "idle", 0.95),
        )
        sprite_scale = 1.25 * scale
        field_radius = int(122 * scale)
        stat_y = int(height * 0.89)
        link_y = int(height * 0.95)
    else:
        title_size, subtitle_size, mono_size = 68, 27, 17
        title_y, subtitle_y = 82, 235
        positions = (
            ("frostbyte", 0.14, 538, "waving", 0.25),
            ("bolt", 0.38, 538, "waving", 0.55),
            ("cinder", 0.62, 538, "running", 0.75),
            ("mantra", 0.86, 538, "idle", 0.95),
        )
        sprite_scale = 1.45 * scale
        field_radius = int(122 * scale)
        stat_y = int(height * 0.86)
        link_y = int(height * 0.94)

    title = font(FONT_BOLD, int(title_size * scale))
    subtitle = font(FONT_REGULAR, int(subtitle_size * scale))
    mono = font(FONT_MONO, int(mono_size * scale))
    draw_centered(draw, int(title_y * scale), "FOUR POWERS.", title, (247, 250, 255, 255), width, stroke=max(2, int(3 * scale)), stroke_fill=(4, 7, 18, 210))
    draw_centered(draw, int((title_y + 76) * scale), "ONE CODEX CREW.", title, (255, 220, 72, 255), width, stroke=max(2, int(3 * scale)), stroke_fill=(4, 7, 18, 210))
    draw_centered(draw, int(subtitle_y * scale), "Ice  •  Lightning  •  Smoke + Ash  •  Mind", subtitle, (192, 214, 242, 245), width)

    for pet, x_ratio, baseline, state, phase in positions:
        center_x = int(width * x_ratio)
        baseline_y = int(baseline * scale)
        draw_power_field(
            image,
            pet,
            center_x,
            baseline_y - int(CELL_H * sprite_scale * 0.45),
            field_radius,
            1.0,
        )
        draw_sprite(
            image,
            pet,
            state,
            phase,
            center_x,
            baseline_y,
            sprite_scale,
        )
        draw_pet_tag(draw, center_x, baseline_y + int(5 * scale), pet, scale * 1.05)

    draw_centered(draw, stat_y, "11 ANIMATION ROWS  •  16 LOOK DIRECTIONS  •  V2", mono, (255, 220, 72, 245), width)
    draw_centered(draw, link_y, "github.com/Ashyboy219/codex-elemental-pets", mono, (194, 212, 238, 235), width)
    image.convert("RGB").save(path, quality=96)


CONTACT_ROWS = (
    ("idle", "idle", 7, "6 + neutral"),
    ("running-right", "running-right", 8, "8 frames"),
    ("running-left", "running-left", 8, "8 frames"),
    ("waving", "waving", 4, "4 frames"),
    ("jumping", "jumping", 5, "5 frames"),
    ("failed", "failed", 8, "8 frames"),
    ("waiting", "waiting", 6, "6 frames"),
    ("running", "running", 6, "6 frames"),
    ("review", "review", 6, "6 frames"),
    ("look-up-to-down", "look 000-157.5", 8, "8 frames"),
    ("look-down-to-up", "look 180-337.5", 8, "8 frames"),
)

DIRECTION_LABELS = (
    "000 up",
    "022.5 up-right",
    "045 up-right",
    "067.5 up-right",
    "090 right",
    "112.5 down-right",
    "135 down-right",
    "157.5 down-right",
    "180 down",
    "202.5 down-left",
    "225 down-left",
    "247.5 down-left",
    "270 left",
    "292.5 up-left",
    "315 up-left",
    "337.5 up-left",
)


def build_waving_gif(pet: str) -> Path:
    output = MEDIA / f"{pet}-waving.gif"
    row, count = ROWS["waving"]
    frames = [
        atlas(pet).crop(
            (
                index * CELL_W,
                row * CELL_H,
                (index + 1) * CELL_W,
                (row + 1) * CELL_H,
            )
        )
        for index in range(count)
    ]
    frames[0].save(
        output,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=140,
        loop=0,
        disposal=2,
        optimize=False,
    )
    return output


def draw_checkerboard(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    tile: int = 12,
) -> None:
    left, top, right, bottom = box
    for y in range(top, bottom, tile):
        for x in range(left, right, tile):
            parity = ((x - left) // tile + (y - top) // tile) % 2
            fill = (246, 246, 246) if parity == 0 else (224, 224, 224)
            draw.rectangle(
                (x, y, min(x + tile - 1, right - 1), min(y + tile - 1, bottom - 1)),
                fill=fill,
            )


def build_contact_sheet(pet: str) -> Path:
    output = MEDIA / f"{pet}-contact-sheet.png"
    columns = 8
    thumb_w, thumb_h = CELL_W // 2, CELL_H // 2
    header_h = 22
    section_h = header_h + thumb_h
    sheet = Image.new("RGB", (columns * thumb_w, len(CONTACT_ROWS) * section_h), (9, 12, 18))
    draw = ImageDraw.Draw(sheet)
    header_font = font(FONT_REGULAR, 11)
    index_font = font(FONT_REGULAR, 9)
    source = atlas(pet)

    for row_index, (_state, label, used, count_label) in enumerate(CONTACT_ROWS):
        y = row_index * section_h
        draw.rectangle((0, y, sheet.width, y + header_h - 1), fill=(8, 10, 14))
        draw.text((4, y + 4), f"row {row_index} {label}", font=header_font, fill=(245, 247, 250))
        count_box = draw.textbbox((0, 0), count_label, font=header_font)
        draw.text((sheet.width - 4 - (count_box[2] - count_box[0]), y + 4), count_label, font=header_font, fill=(245, 247, 250))

        for column in range(columns):
            x = column * thumb_w
            cell_top = y + header_h
            draw_checkerboard(draw, (x, cell_top, x + thumb_w, cell_top + thumb_h))
            border = (34, 199, 133) if column < used else (226, 75, 91)
            draw.rectangle((x, cell_top, x + thumb_w - 1, cell_top + thumb_h - 1), outline=border, width=1)
            if column < used:
                frame = source.crop(
                    (
                        column * CELL_W,
                        row_index * CELL_H,
                        (column + 1) * CELL_W,
                        (row_index + 1) * CELL_H,
                    )
                ).resize((thumb_w, thumb_h), Image.Resampling.NEAREST)
                sheet.paste(frame, (x, cell_top), frame)
            draw.rectangle((x + 1, cell_top + 1, x + 14, cell_top + 13), fill=(250, 250, 250))
            draw.text((x + 3, cell_top + 2), str(column), font=index_font, fill=(20, 23, 28))

    sheet.save(output)
    return output


def paste_direction_frame(
    sheet: Image.Image,
    frame: Image.Image,
    column: int,
    body_top: int,
    zoom: bool,
) -> None:
    if not zoom:
        sheet.paste(frame, (column * CELL_W, body_top), frame)
        return
    alpha_box = frame.getchannel("A").getbbox()
    if alpha_box is None:
        return
    cropped = frame.crop(alpha_box)
    factor = 1.48
    enlarged = cropped.resize(
        (max(1, int(cropped.width * factor)), max(1, int(cropped.height * factor))),
        Image.Resampling.NEAREST,
    )
    x = column * CELL_W + (CELL_W - enlarged.width) // 2
    y = body_top + 7
    sheet.paste(enlarged, (x, y), enlarged)


def build_direction_sheet(pet: str) -> Path:
    output = MEDIA / f"{pet}-directions.png"
    label_h = 26
    section_h = label_h + CELL_H
    sheet = Image.new("RGB", (CELL_W * 8, section_h * 5), (244, 244, 244))
    draw = ImageDraw.Draw(sheet)
    label_font = font(FONT_REGULAR, 11)
    source = atlas(pet)
    neutral = source.crop((6 * CELL_W, 0, 7 * CELL_W, CELL_H))

    groups = (
        ("neutral", (neutral,), False),
        ("normal-row-9", tuple(cell(pet, "look-up-to-down", index) for index in range(8)), False),
        ("normal-row-10", tuple(cell(pet, "look-down-to-up", index) for index in range(8)), False),
        ("zoom-row-9", tuple(cell(pet, "look-up-to-down", index) for index in range(8)), True),
        ("zoom-row-10", tuple(cell(pet, "look-down-to-up", index) for index in range(8)), True),
    )

    for group_index, (kind, frames, zoom) in enumerate(groups):
        section_top = group_index * section_h
        body_top = section_top + label_h
        draw.rectangle((0, body_top, sheet.width, body_top + CELL_H - 1), fill=(238, 238, 238))
        for column, frame in enumerate(frames):
            if kind == "neutral":
                label = "neutral"
            else:
                direction_index = column + (8 if "row-10" in kind else 0)
                prefix = "zoom " if zoom else ""
                label = prefix + DIRECTION_LABELS[direction_index]
            draw.text((column * CELL_W + 5, section_top + 7), label, font=label_font, fill=(20, 20, 20))
            paste_direction_frame(sheet, frame, column, body_top, zoom)

    sheet.save(output)
    return output


def build_pet_exports() -> tuple[Path, ...]:
    waving = []
    for pet in PETS:
        atlas(pet)
        waving.append(build_waving_gif(pet))
        build_contact_sheet(pet)
        build_direction_sheet(pet)
    return tuple(waving)


def build_loops(landscape_video: Path) -> None:
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(landscape_video), "-t", "12",
        "-vf", "fps=10,scale=720:-1:flags=neighbor,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer:bayer_scale=4",
        "-loop", "0", str(MEDIA / "showcase-loop.gif"),
    ], check=True)


def main() -> None:
    MEDIA.mkdir(parents=True, exist_ok=True)
    DOCS_ASSETS.mkdir(parents=True, exist_ok=True)
    waving_gifs = build_pet_exports()
    audio = MEDIA / "original-soundtrack.wav"
    make_audio(audio)
    vertical_video = render_video("showcase-vertical-1080x1920.mp4", (540, 960), (1080, 1920), True, audio)
    landscape_video = render_video("showcase-landscape-1920x1080.mp4", (960, 540), (1920, 1080), False, audio)
    poster(MEDIA / "poster-square-1080x1080.png", 1080, 1080, True)
    poster(MEDIA / "poster-landscape-1200x675.png", 1200, 675, False)
    poster(MEDIA / "poster-vertical-1080x1920.png", 1080, 1920, True)
    build_loops(landscape_video)
    for item in (
        vertical_video,
        landscape_video,
        MEDIA / "poster-square-1080x1080.png",
        MEDIA / "poster-landscape-1200x675.png",
        MEDIA / "poster-vertical-1080x1920.png",
        MEDIA / "showcase-loop.gif",
        *waving_gifs,
    ):
        shutil.copy2(item, DOCS_ASSETS / item.name)
    print("media build complete", flush=True)


if __name__ == "__main__":
    main()
