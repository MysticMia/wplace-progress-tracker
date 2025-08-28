import argparse
import typing

from PIL import Image, ImageDraw
from src.config import load_config, Config
from src.utils.image_utils import Mask
from src.utils.color_utils import ColorName, PIXEL_COLORS, ColorTuple
import os


def _validate_color(color) -> ColorName:
    if color not in PIXEL_COLORS.keys():
        for valid_color in PIXEL_COLORS.keys():
            if valid_color.lower().startswith(color.lower()):
                raise ValueError(
                    f"Invalid color: {color}. "
                    f"Did you mean to use {valid_color} instead? "
                    f"Make sure you type the exact color, and if it contains "
                    f"spaces, place quotation marks around it: "
                    f"\"{valid_color}\"."
                )
        raise ValueError(f"Invalid color: {color}")
    return typing.cast(ColorName, color)


def create_circle_overlay(
        config: Config,
        pixel_colors: list[ColorName],
        circle_radius: int,
        circle_width: int,
        circle_color: ColorTuple,
        background_color: ColorTuple | None = None,
        on_template: bool = False,
) -> Image.Image:
    if circle_radius <= circle_width:
        raise ValueError("Circle radius cannot be smaller than circle width.")

    remaining_pixel_path = os.path.join(config.output_dir,
                                        config.paths.REMAINING_PIXELS_NAME)
    if not os.path.exists(remaining_pixel_path):
        raise ValueError(
            f"File {remaining_pixel_path} does not exist! "
            "Run `main.py` first to create a progress picture."
        )
    remaining_pixels = Image.open(remaining_pixel_path)
    color_mask = Mask.new(remaining_pixels.size)
    for pixel_color in pixel_colors:
        pixel_mask = Mask.from_image_color(remaining_pixels, pixel_color)
        color_mask.union_lighter_color(pixel_mask)

    circle_mask = Mask.new(remaining_pixels.size)
    circle_draw = ImageDraw.Draw(circle_mask)
    # First draw all ellipses, then erase an inner circle (drawing a mask).
    # Doing this instead of drawing circles everywhere means you don't get
    #  a ton of overlapping circles, but rather a bounding box of where
    #  the pixels will be.
    for x, y in color_mask.iterate_predicate(lambda pixel: pixel == 1):
        circle_draw.ellipse(
            xy=(x - circle_radius, y - circle_radius,
                x + circle_radius, y + circle_radius),
            fill="white",
            width=1,
        )
    inner_circle_radius = circle_radius - circle_width
    for x, y in color_mask.iterate_predicate(lambda pixel: pixel == 1):
        circle_draw.ellipse(
            xy=(x - inner_circle_radius, y - inner_circle_radius,
                x + inner_circle_radius, y + inner_circle_radius),
            fill="black",
            width=1,
        )

    just_the_color = Image.new(
        "RGBA", remaining_pixels.size, color=circle_color)

    if on_template:
        canvas = config.get_template_image()
    else:
        canvas = remaining_pixels

    if background_color is not None:
        background = Image.new("RGBA", canvas.size, color=background_color)
        background.paste(canvas, mask=Mask.from_pixel_opacity(canvas))
        canvas = background

    canvas.paste(just_the_color, mask=circle_mask)
    return canvas


def parse_rgba_color(color: str) -> ColorTuple:
    sections = color.split(",")
    if len(sections) != 4:
        raise ValueError(
            f"Invalid color: {color}. Should contain three commas."
        )
    for section in sections:
        if not section.isdecimal():
            raise ValueError(
                f"Invalid color: {color}. Should contain four "
                f"numeric numbers (r,g,b,a)."
            )
    nums = [int(section) for section in sections]
    for section in nums:
        if section < 0 or section > 255:
            raise ValueError(
                f"Invalid color: {color}. Colors should be between 0 and 255."
            )
    return nums[0], nums[1], nums[2], nums[3]


def save_pixel_locator_image(
        config_name: str,
        color_strs: list[str],
        circle_radius: int = 6,
        circle_width: int = 2,
        circle_color_str: str = "255,0,0,255",
        background_color_str: str | None = None,
        on_template: bool = False,
):
    config = load_config(config_name)
    colors = [_validate_color(c) for c in color_strs]
    circle_color = parse_rgba_color(circle_color_str)
    background_color = None
    if background_color_str is not None:
        background_color = parse_rgba_color(background_color_str)
    circle_overlay = create_circle_overlay(
        config=config,
        pixel_colors=colors,
        circle_radius=circle_radius,
        circle_width=circle_width,
        circle_color=circle_color,
        background_color=background_color,
        on_template=on_template,
    )
    output_path = os.path.join(config.output_dir,
                               config.paths.CIRCLE_OVERLAY_NAME)
    circle_overlay.save(output_path)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        description="Make a graph of how many pixels got placed over time."
    )
    arg_parser.add_argument(
        "config",
        type=str,
        help="The config to use."
    )
    arg_parser.add_argument(
        "--pixel_color",
        type=str,
        action="append",
        help="The color to locate. Use quotation marks for colors that "
             "use multiple words: \"Dark Red\"."
    )
    arg_parser.add_argument(
        "--circle_radius",
        type=int,
        default=6,
        help="The radius of the circle to draw around each pixel. "
             "(Default: 6)"
    )
    arg_parser.add_argument(
        "--circle_width",
        type=int,
        default=2,
        help="The width of the circle to draw around each pixel. "
             "(Default: 2)"
    )
    arg_parser.add_argument(
        "--circle_color",
        type=str,
        default="255,0,0,255",
        help="The RGB color of the circle to draw around each pixel. "
             "Should be an \"r,g,b,a\" string. "
             "(Default: 255,0,0,255)"
    )
    arg_parser.add_argument(
        "--on_template",
        action="store_true",
        help="If true, circles are rendered over the template. Otherwise, "
             "circles are rendered over the remaining pixels."
    )
    arg_parser.add_argument(
        "--background_color",
        type=str,
        default="0,0,0,0",
        help="The RGB color of the background, like water or grass. "
             "Use '158,189,255,255' for water. "
             "(Default: 0,0,0,0)"
    )

    args = arg_parser.parse_args()

    save_pixel_locator_image(
        args.config,
        args.pixel_color,
        args.circle_radius,
        args.circle_width,
        args.circle_color,
        args.background_color,
        args.on_template,
    )
