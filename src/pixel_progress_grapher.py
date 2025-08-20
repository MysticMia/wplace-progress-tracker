import argparse
import time
from datetime import datetime
from io import TextIOWrapper

from .config import load_config, Config
from .pixel_utils import ColorName, ColorTuple, PIXEL_COLORS
from typing import Literal, cast, get_args
import os
import matplotlib.pyplot as plt


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


def parse_filename_datetime(filename: str) -> int:
    datetime_str = filename.split(" ", 3)[-1]
    datetime_formatted = datetime.strptime(
        datetime_str,
        '%Y-%m-%dT%H%M%S.txt'
    )
    if datetime_formatted is None:
        raise ValueError(f"Could not parse datetime from filename: {filename}")
    return int(datetime_formatted.timestamp())


def get_data(config: Config):
    data: dict[Literal['time'] | ColorName, list[int]] = {'time': []}
    for pixel_name in get_args(ColorName.__value__):
        data[pixel_name] = []

    for file in os.listdir(config.progress_dir):
        filename = os.fsdecode(file)
        with open(os.path.join(config.progress_dir, filename), 'r') as f:
            data['time'].append(parse_filename_datetime(filename))
            file_data = parse_file(f)
            for key in data:
                if key == 'time':
                    continue
                if key not in file_data:
                    file_data[key] = 0
                data[key].append(file_data[key])
    return data


def pixel_color_to_graph_color(
        pixel_color: ColorTuple
) -> tuple[float, float, float]:
    r, g, b, _ = pixel_color
    return r / 255, g / 255, b / 255


def unix_to_timestring(unix_time: int) -> str:
    return datetime.fromtimestamp(unix_time).strftime('%Y-%m-%d %H:%M')


def make_graph(
        config: Config,
        graph_data: dict[Literal['time'] | ColorName, list[int]]
):
    fig, ax = plt.subplots()
    for key in graph_data:
        if key == 'time':
            continue
        ax.plot(
            graph_data['time'],
            graph_data[key],
            label=key,
            color=pixel_color_to_graph_color(PIXEL_COLORS[key])
        )

    ax.set_title(f"Remaining pixels on '{config.name}'")
    ax.set_xlabel('Time')
    ax.set_ylabel('Pixels left')
    ax.set_xticks(
        graph_data['time'],
        rotation=20,
        # ha='right',
        labels=(unix_to_timestring(i) for i in graph_data['time']),
    )
    # ax.legend()
    fig.subplots_adjust(bottom=0.2)
    path = os.path.join(config.data_directory, "graph.png")
    plt.savefig(path)
    while not os.path.exists(path):
        time.sleep(0.05)


def main(config_name: str):
    config = load_config(config_name)
    data = get_data(config)
    make_graph(config, data)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        description="Graph remaining pixel placements for an artwork."
    )
    arg_parser.add_argument(
        "config",
        type=str,
        help="The config to use."
    )
    args = arg_parser.parse_args()

    main(args.config)
