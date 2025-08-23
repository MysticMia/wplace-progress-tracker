import argparse
import os.path
from PIL import Image

from src.utils.image_utils import get_remaining_pixels
from .config import load_config, Config

REMAINING_PIXELS_NAME = "remaining_pixels.png"


def load_picture(config: Config, progress_picture_name: str):
    progress_path = os.path.join(config.picture_dir, progress_picture_name)

    if not os.path.exists(progress_path):
        raise FileNotFoundError(
            f"Progress image not found! Please add {progress_picture_name} "
            f"to the picture directory (path: {progress_path})."
        )

    return Image.open(progress_path).convert("RGBA")


def main(config_name: str, progress_picture_name: str):
    config = load_config(config_name)

    template = config.get_template_image()
    other = load_picture(config, progress_picture_name)
    remainder_img = get_remaining_pixels(template, other)

    path = os.path.join(config.output_dir, REMAINING_PIXELS_NAME)
    remainder_img.save(path)


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
    main(args.config, args.progress_picture_name)
