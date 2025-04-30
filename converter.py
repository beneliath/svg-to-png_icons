import argparse
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw


# -----------------------------
# Command-Line Interface Setup
# -----------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert SVGs to PNG icons with styling options."
    )
    parser.add_argument(
        "--input-dir", required=True, help="Directory containing SVG files"
    )
    parser.add_argument(
        "--output-dir", required=True, help="Directory to save PNG files"
    )
    parser.add_argument(
        "--color", choices=["white", "black"], default="black", help="Icon color"
    )
    parser.add_argument(
        "--background",
        choices=["black", "white", "transparent"],
        default="transparent",
        help="Button background color",
    )
    parser.add_argument(
        "--button",
        choices=["none", "rounded", "sharp"],
        default="none",
        help="Button shape",
    )
    parser.add_argument(
        "--radius",
        type=int,
        default=10,
        help="Corner radius for rounded buttons (in pixels)",
    )
    parser.add_argument(
        "--size",
        type=str,
        default="100x100",
        help="Resolution, e.g., 100x100 or 512x512",
    )
    parser.add_argument(
        "--dpi", type=int, default=96, help="DPI for PNG rendering (default: 96)"
    )
    parser.add_argument(
        "--padding",
        type=float,
        default=0.1,
        help="Interior padding ratio (0.0 to 0.5) around the image",
    )
    parser.add_argument(
        "--outer-padding",
        type=float,
        default=0.0,
        help="Exterior padding ratio (0.0 to 0.5) around the background button",
    )
    return parser.parse_args()


# -----------------------------
# Create Background Button
# -----------------------------
def create_button_background(size, bg_color, shape, radius):
    bg = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(bg)
    if bg_color == "transparent":
        return bg
    fill_color = (0, 0, 0) if bg_color == "black" else (255, 255, 255)
    if shape == "rounded":
        draw.rounded_rectangle([0, 0, size[0], size[1]], radius=radius, fill=fill_color)
    else:
        draw.rectangle([0, 0, size[0], size[1]], fill=fill_color)
    return bg


# -----------------------------
# Convert and Style Icon
# -----------------------------
def process_svg(
    svg_path,
    output_path,
    icon_color,
    background,
    button_shape,
    radius,
    size,
    dpi,
    padding,
    outer_padding,
):
    temp_png = output_path.with_suffix(".temp.png")
    cairosvg.svg2png(
        url=str(svg_path),
        write_to=str(temp_png),
        output_width=size[0],
        output_height=size[1],
        dpi=dpi,
    )
    icon = Image.open(temp_png).convert("RGBA")
    if icon_color == "white":
        r, g, b, a = icon.split()
        icon = Image.merge(
            "RGBA",
            (
                Image.eval(r, lambda p: 255),
                Image.eval(g, lambda p: 255),
                Image.eval(b, lambda p: 255),
                a,
            ),
        )
    elif icon_color == "black":
        r, g, b, a = icon.split()
        icon = Image.merge(
            "RGBA",
            (
                Image.eval(r, lambda p: 0),
                Image.eval(g, lambda p: 0),
                Image.eval(b, lambda p: 0),
                a,
            ),
        )

    # Compute exterior padding
    ext_pad_x = int(size[0] * outer_padding)
    ext_pad_y = int(size[1] * outer_padding)
    inner_size = (size[0] - 2 * ext_pad_x, size[1] - 2 * ext_pad_y)

    bg = create_button_background(inner_size, background, button_shape, radius)

    # Compute interior (icon) padding
    pad_x = int(inner_size[0] * padding)
    pad_y = int(inner_size[1] * padding)
    target_box = (pad_x, pad_y, inner_size[0] - pad_x, inner_size[1] - pad_y)

    icon = icon.resize(
        (target_box[2] - target_box[0], target_box[3] - target_box[1]), Image.LANCZOS
    )
    bg.paste(icon, box=target_box[:2], mask=icon)

    # Compose on final canvas with exterior padding
    final_image = Image.new("RGBA", size, (0, 0, 0, 0))
    final_image.paste(bg, box=(ext_pad_x, ext_pad_y), mask=bg)
    final_image.save(output_path)
    temp_png.unlink()  # remove temp file


# -----------------------------
# Main Execution
# -----------------------------
def main():
    args = parse_args()
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    width, height = map(int, args.size.lower().split("x"))
    size = (width, height)

    for svg_file in input_dir.glob("*.svg"):
        output_file = output_dir / (svg_file.stem + ".png")
        process_svg(
            svg_file,
            output_file,
            args.color,
            args.background,
            args.button,
            args.radius,
            size,
            args.dpi,
            args.padding,
            args.outer_padding,
        )


if __name__ == "__main__":
    main()
