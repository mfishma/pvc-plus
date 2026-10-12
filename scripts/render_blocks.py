#!/usr/bin/env python3
"""
Renders 16x16 Minecraft block textures into isometric 3D GUI block icons (256x256).
Uses pure Pillow affine transforms matching vanilla Minecraft's GUI orthographic projection.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance


def solve_affine(src_pts, dst_pts):
    """
    Solves for the 6 affine transformation parameters (a, b, c, d, e, f)
    mapping destination (x, y) back to source (u, v):
      u = a*x + b*y + c
      v = d*x + e*y + f
    """
    (x0, y0), (x1, y1), (x2, y2) = dst_pts
    (u0, v0), (u1, v1), (u2, v2) = src_pts
    det = x0 * (y1 - y2) + x1 * (y2 - y0) + x2 * (y0 - y1)

    a = (u0 * (y1 - y2) + u1 * (y2 - y0) + u2 * (y0 - y1)) / det
    b = (u0 * (x2 - x1) + u1 * (x0 - x2) + u2 * (x1 - x0)) / det
    c = (u0 * (x1 * y2 - x2 * y1) + u1 * (x2 * y0 - x0 * y2) + u2 * (x0 * y1 - x1 * y0)) / det

    d = (v0 * (y1 - y2) + v1 * (y2 - y0) + v2 * (y0 - y1)) / det
    e = (v0 * (x2 - x1) + v1 * (x0 - x2) + v2 * (x1 - x0)) / det
    f = (v0 * (x1 * y2 - x2 * y1) + v1 * (x2 * y0 - x0 * y2) + v2 * (x0 * y1 - x1 * y0)) / det
    return (a, b, c, d, e, f)


def render_isometric_block(tex_path: Path, out_path: Path, size: int = 256) -> None:
    """Renders a single 16x16 texture into an isometric 3D block cube."""
    src = Image.open(tex_path).convert("RGBA")

    # Pad border to prevent alpha-edge bleeding during affine transforms
    pad = 4
    padded = Image.new("RGBA", (src.width + 2 * pad, src.height + 2 * pad))
    padded.paste(src, (pad, pad))
    for x in range(padded.width):
        for y in range(padded.height):
            cx = max(pad, min(pad + src.width - 1, x))
            cy = max(pad, min(pad + src.height - 1, y))
            padded.putpixel((x, y), padded.getpixel((cx, cy)))

    # Nearest-neighbor scaling for authentic pixel art
    scale = 16
    padded = padded.resize((padded.width * scale, padded.height * scale), Image.NEAREST)

    u_min, v_min = pad * scale, pad * scale
    u_max, v_max = (pad + src.width) * scale, (pad + src.height) * scale
    src_pts = [(u_min, v_min), (u_max, v_min), (u_min, v_max)]

    # Standard Minecraft GUI block projection vertices (256x256 bounding box)
    v_top = (127, 2)
    v_left = (15, 66)
    v_right = (240, 66)
    v_center = (127, 130)
    v_bot_left = (15, 189)
    v_bot_right = (240, 189)
    v_bot = (127, 253)

    def shade(img, factor):
        r, g, b, a = img.split()
        rgb = ImageEnhance.Brightness(Image.merge("RGB", (r, g, b))).enhance(factor)
        r2, g2, b2 = rgb.split()
        return Image.merge("RGBA", (r2, g2, b2, a))

    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    # 1. Left Face (60% lighting)
    c_left = solve_affine(src_pts, [v_left, v_center, v_bot_left])
    img_left = shade(padded, 0.6).transform((size, size), Image.AFFINE, c_left, Image.NEAREST)
    mask_left = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask_left).polygon([v_left, v_center, v_bot, v_bot_left], fill=255)
    img_left.putalpha(mask_left)
    canvas = Image.alpha_composite(canvas, img_left)

    # 2. Right Face (80% lighting)
    c_right = solve_affine(src_pts, [v_center, v_right, v_bot])
    img_right = shade(padded, 0.8).transform((size, size), Image.AFFINE, c_right, Image.NEAREST)
    mask_right = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask_right).polygon([v_center, v_right, v_bot_right, v_bot], fill=255)
    img_right.putalpha(mask_right)
    canvas = Image.alpha_composite(canvas, img_right)

    # 3. Top Face (100% lighting)
    c_top = solve_affine(src_pts, [v_top, v_right, v_left])
    img_top = shade(padded, 1.0).transform((size, size), Image.AFFINE, c_top, Image.NEAREST)
    mask_top = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask_top).polygon([v_top, v_right, v_center, v_left], fill=255)
    img_top.putalpha(mask_top)
    canvas = Image.alpha_composite(canvas, img_top)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)
    print(f"Rendered: {out_path.name}")


def main():
    repo_root = Path(__file__).resolve().parent.parent
    textures_dir = repo_root / "assets" / "pvc-plus" / "textures" / "item"
    output_dir = repo_root / ".github" / "images"

    protection_textures = [
        "protection_copper_ore.png",
        "protection_lapis_ore.png",
        "protection_nether_gold_ore.png",
        "protection_coal_ore.png",
        "protection_redstone_ore.png",
        "protection_diamond_ore.png",
        "protection_deepslate_emerald_ore.png",
    ]

    for tex_name in protection_textures:
        tex_path = textures_dir / tex_name
        if tex_path.exists():
            out_path = output_dir / tex_name
            render_isometric_block(tex_path, out_path)
        else:
            print(f"Warning: Texture not found: {tex_path}")


if __name__ == "__main__":
    main()
