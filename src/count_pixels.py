import argparse
import os.path

from src.utils.image_utils import get_pixel_count
from .config import load_config, Config
from PIL import Image
from src.utils.color_utils import ColorName


def _save_pixel_count_data(config: Config, data: dict[ColorName, int]):
    path = os.path.join(config.output_dir,
                        config.paths.REMAINING_PIXEL_COUNT_NAME)
    with open(path, "w") as f:
        max_key_length = max(len(key) for key in data.keys())
        for key, value in data.items():
            f.write(f"{key:>{max_key_length}}: {value}\n")


def save_pixel_count(config: Config):
    image_path = os.path.join(config.output_dir,
                              config.paths.REMAINING_PIXELS_NAME)
    img = Image.open(image_path)

    pixel_count = get_pixel_count(img)
    _save_pixel_count_data(config, pixel_count)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        description="Count how often pixels occur in a wplace image."
    )
    arg_parser.add_argument(
        "config",
        type=str,
        help="The config file to use."
    )

    args = arg_parser.parse_args()

    save_pixel_count(load_config(args.config))
