import argparse
from datetime import datetime
from io import TextIOWrapper

from src.utils.image_utils import get_pixel_count
from .config import load_config, Config
from src.utils.color_utils import ColorName, ColorTuple, PIXEL_COLORS
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


def get_progress_data(
        config: Config
) -> dict[Literal['time'] | ColorName, list[int]]:
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


def convert_progress_data_to_percentage(
        config: Config,
        progress_data: dict[Literal['time'] | ColorName, list[int]]
) -> dict[Literal['time'] | ColorName, list[float]]:
    template_image = config.get_template_image()
    pixel_counts: dict[ColorName, int] = get_pixel_count(template_image)
    percentage_data: dict[Literal['time'] | ColorName, list[float]] = {}
    for key in progress_data:
        if key == "Transparent":
            # I don't think people care about transparent pixels here.
            continue
        if key == 'time':
            percentage_data[key] = [float(i) for i in progress_data[key]]
            continue
        pixel_count = pixel_counts[key]
        if pixel_count == 0:
            percentage_data[key] = [0.0 for _ in progress_data[key]]
            continue
        percentage_data[key] = [round(i * 100 / pixel_count, 2)
                                for i in progress_data[key]]

    return percentage_data



def pixel_color_to_graph_color(
        pixel_color: ColorTuple
) -> tuple[float, float, float]:
    r, g, b, _ = pixel_color
    return r / 255, g / 255, b / 255


def unix_to_timestring(unix_time: int) -> str:
    return datetime.fromtimestamp(unix_time).strftime('%Y-%m-%d %H:%M')


def select_data_by_time(
        data: (dict[Literal['time'] | ColorName, list[int]]
               | dict[Literal['time'] | ColorName, list[float]]),
        earliest_bound: int,
        latest_bound: int
) -> (dict[Literal['time'] | ColorName, list[int]]
      | dict[Literal['time'] | ColorName, list[float]]):
    assert "time" in data.keys(), "Missing \"time\" key!"
    keys, values = zip(*data.items())
    time_index = keys.index("time")

    # Find index bounds
    minimum_index = None
    maximum_index = None
    for index, val in enumerate(values[time_index]):
        if minimum_index is None and val >= earliest_bound:
            # `is None` because we only want the first value, so don't update
            #  it once it has been set.
            minimum_index = index
        if val <= latest_bound:
            maximum_index = index + 1

    # Note: you can take slices with None: "apple"[None:None] == "apple"

    values = [plot[minimum_index:maximum_index] for plot in values]
    return dict(zip(keys, values))


def make_graph(
        config: Config,
        graph_data: (dict[Literal['time'] | ColorName, list[int]]
                     | dict[Literal['time'] | ColorName, list[float]]),
        max_minutes: int | None = None
):
    fig, ax = plt.subplots()
    only_one_data_point = True

    if max_minutes is not None:
        now_unix = int(datetime.now().timestamp())
        max_minutes_unix = now_unix - max_minutes * 60
        graph_data = select_data_by_time(graph_data, max_minutes_unix, now_unix)

    for key in graph_data:
        if key == 'time':
            continue
        if len(graph_data[key]) > 1:
            only_one_data_point = False
        # Don't plot graphs once they reached zero.
        if graph_data[key][0] == 0:
            # This graph will be entirely zeros so might as well ignore it.
            continue
        line_data = [
            float('nan')
            if i > 0 and graph_data[key][i - 1] == 0
            # ^ if the previous point is 0, the one point should also be 0
            #  too: We won't need to plot the 'zero' points
            #  after the first one.
            else graph_data[key][i]
            for i in range(len(graph_data[key]))  # from index 1: i-1>=0
        ]
        line_color = pixel_color_to_graph_color(PIXEL_COLORS[key])
        if line_color == (1, 1, 1):
            # Display white as a dotted black line (on a white background)
            line_style = "dotted"
            line_color = (0, 0, 0)
        else:
            line_style = "solid"
        ax.plot(
        # ax.step(
            graph_data['time'],
            line_data,
            label=key,
            color=line_color,
            linestyle=line_style,
        )
    if only_one_data_point:
        print(
            "You only have one data point so far. This means your graph will "
            "not have any graphs displayed on them yet. Gather more progress "
            "data to see graphs."
        )

    ax.set_title(f"Remaining pixels on '{config.name}'")
    ax.set_xlabel('Time')
    ax.set_ylabel('Pixels left')
    ax.set_xlim(min(graph_data['time']), max(graph_data['time']))
    ax.set_ylim(
        0,
        max(
            graph_data[key][0] for key in graph_data
            if (key != "Transparent"
                and key != 'time')
        )*1.05)
    # ax.set_xticks(
    #     graph_data['time'],
    #     rotation=20,
    #     # ha='right',
    #     labels=(unix_to_timestring(i) for i in graph_data['time']),
    # )

    def formatter(x, _):
        return unix_to_timestring(x)

    ax.xaxis.set_major_formatter(formatter)
    ax.tick_params(axis='x', labelrotation=20)
    # ax.legend()
    fig.subplots_adjust(bottom=0.2)
    path = os.path.join(config.output_dir, "graph.png")
    plt.savefig(path)


def save_pixel_progress_graph(
        config_name: str,
        max_minutes: int | None = None
):
    config = load_config(config_name)
    data = get_progress_data(config)
    # data = convert_progress_data_to_percentage(config, data)
    make_graph(config, data, max_minutes=max_minutes)


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
    args = arg_parser.parse_args()

    save_pixel_progress_graph(args.config, args.max_minutes)
