import argparse
import os.path
from PIL import Image

from src.config import load_config, Config
from src.utils.image_utils import (
    get_remaining_pixels_image,
    filter_colors,
    Mask,
)

REMAINING_PIXELS_NAME = "remaining_pixels.png"
REMAINING_PLACEABLE_PIXELS_NAME = "remaining_pixels_placeable.png"
REMAINING_UNPLACEABLE_PIXELS_NAME = "remaining_pixels_unplaceable.png"


def get_progress(
        template: Image.Image,
        remainder_image: Image.Image
) -> float:
    template_mask = Mask.from_pixel_opacity(template)
    # ^ White for placed pixels, black for unplaced / transparent pixels.
    remaining_mask = Mask.from_pixel_opacity(remainder_image)
    # ^ White for unplaced pixels, black for placed / transparent pixels.

    template_count = template_mask.count().get(255, 0)  # get total pixels
    remaining_count = remaining_mask.count().get(255, 0)  # get unplaced pixels

    remaining_progress = remaining_count / template_count
    return 1 - remaining_progress


def load_picture(config: Config, progress_picture_name: str):
    progress_path = os.path.join(config.picture_dir, progress_picture_name)

    if not os.path.exists(progress_path):
        raise FileNotFoundError(
            f"Progress image not found! Please add {progress_picture_name} "
            f"to the picture directory (path: {progress_path})."
        )

    return Image.open(progress_path).convert("RGBA")


def save_remainder_images(config: Config, progress_picture_name: str):
    template = config.get_template_image()
    other = load_picture(config, progress_picture_name)

    remainder_img = get_remaining_pixels_image(template, other)
    path = os.path.join(config.output_dir,
                        config.paths.REMAINING_PIXELS_NAME)
    remainder_img.save(path)

    available = filter_colors(remainder_img,
                              list(config.available_colors.keys()))
    path = os.path.join(config.output_dir,
                        config.paths.REMAINING_PLACEABLE_PIXELS_NAME)
    available.save(path)

    unavailable = filter_colors(remainder_img,
                                list(config.unavailable_colors.keys()))
    path = os.path.join(config.output_dir,
                        config.paths.REMAINING_UNPLACEABLE_PIXELS_NAME)

    progress = get_progress(template, remainder_img)
    print(f"The template has been built for {progress:.2%}.")

    unavailable.save(path)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        description="Get the remaining pixels using the template and a "
                    "progress image."
    )
    arg_parser.add_argument(
        "config",
        type=str,
        help="The config to use for the template."
    )
    arg_parser.add_argument(
        "progress_picture_name",
        type=str,
        help="The progress picture name to compare to."
    )

    args = arg_parser.parse_args()
    save_remainder_images(
        load_config(args.config),
        args.progress_picture_name
    )
