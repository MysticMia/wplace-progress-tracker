import argparse
import os.path

from .config import load_config, Config
from PIL import Image
from .pixel_utils import get_pixel_colors, ColorName, ColorTuple


def get_pixel_count(img: Image.Image) -> dict[ColorName, int]:
    assert img.mode == "RGBA", "Image is expected to be RGBA!"
    name_table: dict[ColorTuple, ColorName] = {
        v: k
        for k, v in get_pixel_colors().items()
    }
    pixel_count: dict[ColorName, int] = {k: 0 for k in name_table.values()}
    for x in range(img.width):
        for y in range(img.height):
            pixel: ColorTuple = img.getpixel((x, y))  # type: ignore
            pixel = (pixel[0], pixel[1], pixel[2], pixel[3]//255)
            pixel_name = name_table[pixel]
            pixel_count[pixel_name] += 1

    del pixel_count["Transparent"]
    sorted_pixel_count = dict(sorted(
        pixel_count.items(),
        key=lambda i: i[1],
        reverse=True
    ))
    return sorted_pixel_count


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
