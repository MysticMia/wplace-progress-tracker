import argparse
import typing

from PIL import Image
from src.config import load_config, Config
from src.utils.image_utils import get_pixel_count
from src.utils.color_utils import ColorName
from src.utils.graphing_utils import Grapher, parse_filename_unix_time
import os


def _get_image_paths(config: Config):
    image_paths = []
    for image_path in os.listdir(config.picture_dir):
        assert image_path.endswith(".png"), (
            f"Expected .png file, got {image_path}!"
        )
        image_paths.append(image_path)
    print(len(image_paths))
    image_paths.sort()  # dir/yyyy-mm-dd hh-mm-ss format should sort alphabetically.
    return image_paths


TIME_INTERVAL = 30


def put_average_placement_data(
        config: Config,
        grapher: Grapher,
) -> None:
    image_paths = _get_image_paths(config)

    previous_image_count: dict[ColorName, int] | None = None
    previous_image_time: int | None = None
    for image_name in image_paths:
        path = os.path.join(config.picture_dir, image_name)
        img = Image.open(path)
        count = get_pixel_count(img)
        image_time = parse_filename_unix_time(image_name)
        if previous_image_count is None:
            previous_image_count = count
            previous_image_time = image_time
            continue

        previous_image_count = typing.cast(dict[ColorName, int],
                                           previous_image_count)
        previous_image_time = typing.cast(int, previous_image_time)
        assert count.keys() == previous_image_count.keys()

        timespan = (image_time - previous_image_time)
        count_difference: dict[ColorName, float] = {
            k: (v - previous_image_count[k]) * 60 / timespan
            for k, v in count.items()
        }
        grapher.add_data_point_from_filename(image_name, count_difference)
        previous_image_count = count


def save_average_placement_graph(
        config_name: str,
        max_minutes: int | None = None,
        step_graph: bool = False,
):
    config = load_config(config_name)
    grapher = Grapher()
    put_average_placement_data(config, grapher)
    grapher.make_graph(
        config,
        config.paths.AVERAGE_PIXEL_PLACEMENT_GRAPH_NAME,
        title=f"Pixels placed on '{config.name}'",
        y_axis_label="Pixels per minute",
        max_minutes=max_minutes,
        as_step=step_graph,
        hide_repeating_zeros=False,
    )


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
        "--max_minutes",
        type=int,
        default=None,
        help="How far back in time to make the graph, in minutes. "
             "(default: No limit)"
    )
    arg_parser.add_argument(
        "--step_graph",
        action="store_true",
        help="Whether to make the graph as steps or as a line. "
             "(Default: Line graph)"
    )

    args = arg_parser.parse_args()

    save_average_placement_graph(
        args.config,
        args.max_minutes,
        args.step_graph,
    )
