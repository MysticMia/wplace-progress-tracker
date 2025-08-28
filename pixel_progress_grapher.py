import argparse
import types
from io import TextIOWrapper

from src.utils.graphing_utils import Grapher
from src.utils.image_utils import get_pixel_count
from src.config import load_config, Config
from src.utils.color_utils import ColorName, PIXEL_COLORS
from typing import Literal, cast
from PIL import Image
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


def put_progress_data(
        config: Config,
        grapher: Grapher,
        as_progress: bool,
) -> None:
    template = config.get_template_image()
    template_count = get_pixel_count(template)

    for file in os.listdir(config.picture_dir):
        filename = os.fsdecode(file)
        image_path = os.path.join(config.picture_dir, filename)
        img = Image.open(image_path)

        color_data = get_pixel_count(img)
        if not as_progress:
            color_data: dict[ColorName, int] = {
                k: template_count[k] - v
                for k, v in color_data.items()
            }

        grapher.add_data_point_from_filename(filename, color_data)


def convert_progress_data_to_percentage(
        config: Config,
        grapher: Grapher,
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
        as_step: bool = False,
        as_progress: bool = False,
        as_percentage: bool = False,
):
    config = load_config(config_name)
    grapher = Grapher()
    put_progress_data(config, grapher, as_progress)

    if as_percentage:
        convert_progress_data_to_percentage(config, grapher)

    y_label = "Remaining pixels" + (" (%)" if as_percentage else "")
    grapher.make_graph(
        config,
        f"Remaining pixels on '{config.name}'",
        y_label,
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
        "--as_progress",
        action="store_true",
        help="Whether to track progress or track remaining pixels. "
             "(Default: Remaining pixels, add this flag to track "
             "progress instead.)"
    )
    arg_parser.add_argument(
        "--max_minutes",
        type=int,
        default=None,
        help="How far back in time to make the graph, in minutes. "
             "(Default: No limit)"
    )
    arg_parser.add_argument(
        "--as_step",
        action="store_true",
        help="Whether to make the graph as steps or as a line. "
             "(Default: Line graph)"
    )
    arg_parser.add_argument(
        "--as_percentage",
        action="store_true",
        help="Display each plot as a percentage of the placed pixels from the "
             "total pixels from the template image."
    )
    args = arg_parser.parse_args()

    save_pixel_progress_graph(
        args.config,
        args.max_minutes,
        args.as_step,
        args.as_progress,
        args.as_percentage,
    )
