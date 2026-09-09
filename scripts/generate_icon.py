"""
scripts/generate_icon.py
--------------------------
Generates the Agentic-AI-OS app icon programmatically (no external art
assets) as a multi-resolution .ico for the window/taskbar icon and the
packaged .exe, plus a standalone PNG for other uses (tray icon, docs).

Design: a rounded "squircle" with a deep navy-to-indigo-to-cyan gradient
(futuristic tech palette) and a minimal connected-node glyph in the center,
representing an orchestration/agent network. Run once; commit the output.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFilter

SIZE = 1024
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

# Futuristic dark-tech palette.
COLOR_TOP = (10, 14, 26)       # near-black navy
COLOR_MID = (67, 56, 202)      # indigo
COLOR_BOTTOM = (6, 182, 212)   # cyan
GLYPH_COLOR = (240, 246, 255)  # near-white
GLYPH_ACCENT = (103, 232, 249) # light cyan


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _gradient_background(size: int) -> Image.Image:
    img = Image.new("RGB", (size, size))
    px = img.load()
    for y in range(size):
        t = y / (size - 1)
        if t < 0.55:
            color = _lerp(COLOR_TOP, COLOR_MID, t / 0.55)
        else:
            color = _lerp(COLOR_MID, COLOR_BOTTOM, (t - 0.55) / 0.45)
        for x in range(size):
            px[x, y] = color
    return img


def _rounded_mask(size: int, radius_ratio: float = 0.24) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    radius = int(size * radius_ratio)
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return mask


def _draw_node_glyph(draw: ImageDraw.ImageDraw, size: int) -> None:
    center = size / 2
    r = size * 0.30  # ring radius the nodes sit on
    node_r = size * 0.052
    hub_r = size * 0.062
    line_w = max(2, int(size * 0.012))

    # Three outer nodes at 90/210/330 degrees, one central hub — a minimal
    # "orchestrator + agents" motif.
    angles = [-90, 30, 150]
    points = [
        (center + r * math.cos(math.radians(a)), center + r * math.sin(math.radians(a)))
        for a in angles
    ]

    for px_, py_ in points:
        draw.line([(center, center), (px_, py_)], fill=GLYPH_ACCENT, width=line_w)

    for px_, py_ in points:
        draw.ellipse(
            [px_ - node_r, py_ - node_r, px_ + node_r, py_ + node_r],
            fill=GLYPH_COLOR,
        )

    draw.ellipse(
        [center - hub_r, center - hub_r, center + hub_r, center + hub_r],
        fill=GLYPH_COLOR,
    )


def build_icon() -> Image.Image:
    bg = _gradient_background(SIZE).convert("RGBA")
    mask = _rounded_mask(SIZE)

    # Subtle inner glow behind the glyph for depth.
    glow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_r = SIZE * 0.38
    center = SIZE / 2
    glow_draw.ellipse(
        [center - glow_r, center - glow_r, center + glow_r, center + glow_r],
        fill=(255, 255, 255, 40),
    )
    glow = glow.filter(ImageFilter.GaussianBlur(SIZE * 0.06))
    bg = Image.alpha_composite(bg, glow)

    draw = ImageDraw.Draw(bg)
    _draw_node_glyph(draw, SIZE)

    # Thin outer border for definition against light/dark desktop backgrounds.
    border = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ImageDraw.Draw(border).rounded_rectangle(
        [2, 2, SIZE - 3, SIZE - 3], radius=int(SIZE * 0.24), outline=(255, 255, 255, 60), width=max(2, SIZE // 256)
    )
    bg = Image.alpha_composite(bg, border)

    out = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    out.paste(bg, (0, 0), mask)
    return out


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    icon = build_icon()

    png_path = os.path.join(OUT_DIR, "icon.png")
    icon.save(png_path)

    ico_path = os.path.join(OUT_DIR, "icon.ico")
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    icon.save(ico_path, sizes=sizes)

    print(f"Wrote {png_path}")
    print(f"Wrote {ico_path}")


if __name__ == "__main__":
    main()
