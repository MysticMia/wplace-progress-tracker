import os.path
from typing import Literal, get_args

from src.utils.color_utils import ColorName, ColorTuple, PIXEL_COLORS
from datetime import datetime
from matplotlib import pyplot as plt
from src.config import Config


def _pixel_color_to_graph_color(
        pixel_color: ColorTuple
) -> tuple[float, float, float]:
    r, g, b, _ = pixel_color
    return r / 255, g / 255, b / 255


def _parse_filename_datetime(filename: str) -> int:
    datetime_str = filename.split(".", 3)[0]
    datetime_formatted = datetime.strptime(
        datetime_str,
        '%Y-%m-%dT%H%M%S'
    )
    if datetime_formatted is None:
        raise ValueError(f"Could not parse datetime from filename: {filename}")
    return int(datetime_formatted.timestamp())


def _unix_to_timestring(unix_time: int) -> str:
    return datetime.fromtimestamp(unix_time).strftime('%Y-%m-%d %H:%M')


class Grapher:
    def __init__(self):
        self.data: (
                dict[Literal['time'] | ColorName, list[float]]
        ) = {'time': []}
        for pixel_name in get_args(ColorName.__value__):
            self.data[pixel_name] = []

    def add_data_point(
            self,
            time: int,
            appended_data: dict[ColorName, int],
    ) -> None:
        # Todo: this is a duplicate
        for key in self.data:
            if key == "time":
                self.data["time"].append(time)
            else:
                self.data[key].append(
                    appended_data.get(key, 0)
                )

    def add_data_point_from_filename(
            self,
            filename: str,
            appended_data: dict[ColorName, int],
    ) -> None:
        """
        Helper to run `add_data_point` with a filename, instead of
        unix timestamp.

        :param filename: The name to parse to unix timestamp.
        :param appended_data: The data point to append.
        """
        self.add_data_point(
            _parse_filename_datetime(filename),
            appended_data
        )

    def crop_data_to_time_range(
            self,
            earliest_bound: int,
            latest_bound: int
    ) -> None:
        assert "time" in self.data.keys(), "Missing \"time\" key!"
        keys, values = zip(*self.data.items())
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
        self.data = dict(zip(keys, values))

    def hide_repeating_zeros_data(self) -> None:
        for key in self.data:
            if key == 'time':
                continue
            self.data[key] = [
                float('nan')
                if i > 0 and self.data[key][i - 1] == 0
                # ^ if the previous point is 0, the one point should also be 0
                #  too: We won't need to plot the 'zero' points
                #  after the first one.
                else self.data[key][i]
                for i in range(len(self.data[key]))  # from index 1: i-1>=0
            ]

    def make_graph(
            self,
            config: Config,
            title: str,
            y_axis_label: str,
            *,
            max_minutes: int | None = None,
            as_step: bool = False,
            hide_repeating_zeros: bool = True,
    ):
        fig, ax = plt.subplots()
        only_one_data_point = True

        if max_minutes is not None:
            now_unix = int(datetime.now().timestamp())
            max_minutes_unix = now_unix - max_minutes * 60
            self.crop_data_to_time_range(max_minutes_unix, now_unix)

        if hide_repeating_zeros:
            self.hide_repeating_zeros_data()

        for key in self.data:
            if key == 'time':
                continue
            if len(self.data[key]) > 1:
                only_one_data_point = False
            # Don't plot graphs once they reached zero.
            if self.data[key][0] == 0:
                # This graph will be entirely zeros so might as well ignore it.
                continue
            line_color = _pixel_color_to_graph_color(PIXEL_COLORS[key])
            if line_color == (1, 1, 1):
                # Display white as a dotted black line (on a white background)
                line_style = "dotted"
                line_color = (0, 0, 0)
            else:
                line_style = "solid"

            if as_step:
                ax.step(
                    self.data['time'],
                    self.data[key],
                    label=key,
                    color=line_color,
                    linestyle=line_style,
                    where="post",
                )
            else:
                ax.plot(
                    self.data['time'],
                    self.data[key],
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

        ax.set_title(title)
        ax.set_xlabel('Time')
        ax.set_ylabel(y_axis_label)
        ax.set_xlim(min(self.data['time']), max(self.data['time']))
        ax.set_ylim(
            min(
                min(self.data[key]) for key in self.data
                if (key != "Transparent"
                    and key != 'time')
            ) * 1.05,
            max(
                max(self.data[key]) for key in self.data
                if (key != "Transparent"
                    and key != 'time')
            ) * 1.05)

        # ax.set_xticks(
        #     self.data['time'],
        #     rotation=20,
        #     # ha='right',
        #     labels=(unix_to_timestring(i) for i in self.data['time']),
        # )

        def formatter(x, _):
            return _unix_to_timestring(x)

        ax.xaxis.set_major_formatter(formatter)
        ax.tick_params(axis='x', labelrotation=20)
        # ax.legend()
        fig.subplots_adjust(bottom=0.2)
        path = os.path.join(config.output_dir, "graph.png")
        plt.savefig(path)
