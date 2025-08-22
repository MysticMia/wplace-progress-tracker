import argparse
import os.path

from src.utils.image_utils import get_pixel_count
from .config import load_config, Config
from PIL import Image
from src.utils.color_utils import ColorName


def save_pixel_count(config: Config, name: str, data: dict[ColorName, int]):
    path = os.path.join(config.progress_dir, name)
    with open(path, "w") as f:
        for key, value in data.items():
            f.write(f"{key}, {value}\n")


def main(config_name: str, file_name: str):
    config = load_config(config_name)

    image_path = os.path.join(
        config.data_directory,
        f"remaining_pixels.png"
    )
    img = Image.open(image_path)
    pixel_count = get_pixel_count(img)

    save_pixel_count(config, f"{file_name}.txt", pixel_count)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        description="Count how often pixels occur in a wplace image."
    )
    arg_parser.add_argument(
        "config",
        type=str,
        help="The config file to use."
    )
    arg_parser.add_argument(
        "file_timestamp",
        type=str,
        help="The file to count (datetime)."
    )

    args = arg_parser.parse_args()

    main(args.config, args.file_timestamp)
