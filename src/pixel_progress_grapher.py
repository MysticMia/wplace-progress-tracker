import argparse
from datetime import datetime
from io import TextIOWrapper

from src.utils.graphing_utils import Grapher
from src.utils.image_utils import get_pixel_count
from .config import load_config, Config
from src.utils.color_utils import ColorName
from typing import Literal, cast
import os


def parse_file(text: TextIOWrapper) -> dict[ColorName, int]:
    file_data: dict[ColorName, int] = {}
    for line in text:
        pixel_data = line.split(",")
        assert len(pixel_data) == 2, \
            f"Expected {line} to be made of 2 components!"
        pixel_data = [i.strip() for i in pixel_data]
        color_name = cast(ColorName, pixel_data[0])
        file_data[color_name] = int(pixel_data[1])
    return file_data


def get_progress_data(
        config: Config,
        grapher: Grapher,
) -> None:
    for file in os.listdir(config.progress_dir):
        filename = os.fsdecode(file)
        path = os.path.join(config.progress_dir, filename)
        with open(path, 'r') as f:
            file_data = parse_file(f)
            grapher.add_data_point_from_filename(filename, file_data)


def convert_progress_data_to_percentage(
        config: Config,
        grapher: Grapher
) -> None:
    template_image = config.get_template_image()
    pixel_counts: dict[ColorName, int] = get_pixel_count(template_image)
    percentage_data: dict[Literal['time'] | ColorName, list[float]] = {}
    for key in grapher.data:
        if key == "Transparent":
            # I don't think people care about transparent pixels here.
            continue
        if key == 'time':
            percentage_data[key] = [float(i) for i in grapher.data[key]]
            continue
        pixel_count = pixel_counts[key]
        if pixel_count == 0:
            percentage_data[key] = [0.0 for _ in grapher.data[key]]
            continue
        percentage_data[key] = [round(i * 100 / pixel_count, 2)
                                for i in grapher.data[key]]

    grapher.data = percentage_data


def save_pixel_progress_graph(
        config_name: str,
        max_minutes: int | None = None,
        as_step: bool = False
):
    config = load_config(config_name)
    grapher = Grapher()
    get_progress_data(config, grapher)
    # data = convert_progress_data_to_percentage(config, data)
    grapher.make_graph(
        config,
        f"Remaining pixels on '{config.name}'",
        "Remaining pixels (%)",
        max_minutes=max_minutes,
        as_step=as_step
    )


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        description="Graph remaining pixel placements for an artwork."
    )
    arg_parser.add_argument(
        "config",
        type=str,
        help="The config to use."
    )
    arg_parser.add_argument(
        "--max_minutes",
        type=int,
        default=None,
        help="How far to go back in time, in minutes."
    )
    arg_parser.add_argument(
        "--as_step",
        action="store_true",
        help="How far to go back in time, in minutes."
    )
    args = arg_parser.parse_args()

    save_pixel_progress_graph(
        args.config,
        args.max_minutes,
        args.as_step,
    )
