import argparse
import os.path
from PIL import Image

from src.config import load_config, Config
from src.utils.color_utils import ColorName
from src.utils.image_utils import get_pixel_count


def _save_pixel_count_data(
        config: Config,
        remainder_data: dict[ColorName, int],
        template_data: dict[ColorName, int],
):
    path = os.path.join(config.output_dir,
                        config.paths.REMAINING_PIXEL_COUNT_NAME)

    # sort data by progress and goal count
    remainder_data = dict(sorted(
            remainder_data.items(),
            key=lambda item: (item[1], template_data[item[0]]),
            reverse=True,
    ))

    with (open(path, "w") as f):
        max_key_length = max(len(key) for key in remainder_data.keys())
        max_remainder_count_length = len(str(
            max(val for val in remainder_data.values())))
        max_template_count_length = len(str(
            max(val for val in template_data.values())))

        f.write(
            f"{'Color':^{max_key_length - 1}}"
            f"{'Remaining':<{max_remainder_count_length}}    "
            f"{'Current':<{max_template_count_length}}   "
            f"{'Goal':<{max_template_count_length}}    "
            f"Progress%  "
            f"Pixel ownership"
            f"\n"
        )
        placed_count = (sum(template_data.values())
                        - sum(remainder_data.values()))
        f.write(
            f"{'All':<{max_key_length}} "
            f"{sum(remainder_data.values())
            :>{max_remainder_count_length + 2}}"
            f"    "
            f"{placed_count:>{max_template_count_length + 2}} / "
            f"{sum(template_data.values())
            :<{max_template_count_length + 2}} = "
            f"{(placed_count * 100 / sum(template_data.values()))
            if sum(template_data.values()) > 0 else 100:6.2f}%\n\n"
        )

        for key, remaining_count in remainder_data.items():
            goal_count = template_data[key]
            current_count = goal_count - remaining_count
            progress = (100 * current_count / goal_count
                        ) if goal_count > 0 else 100

            if key in config.bought_colors:
                suffix = "Bought"
            elif key in config.available_colors:
                # free + bought = available
                #  Therefore: available - bought = free
                suffix = "Free"
            else:
                suffix = "Premium"


            f.write(
                f"{key:<{max_key_length}} : "
                f"{remaining_count:>{max_remainder_count_length}}"
                f"      "
                f"{current_count:>{max_template_count_length}} / "
                f"{goal_count:<{max_template_count_length}}   = "
                f"{progress:6.2f}%      "
                # ^ 9.329 -> 9.33 -> "  9.33" (len = 6, decimals = 2) -> 6.2f
                f"{suffix}"
                f"\n"
            )


def save_pixel_count(config: Config):
    image_path = os.path.join(config.output_dir,
                              config.paths.REMAINING_PIXELS_NAME)
    template = config.get_template_image()
    img = Image.open(image_path)

    remaining_pixel_count = get_pixel_count(img)
    goal_pixel_count = get_pixel_count(template)
    _save_pixel_count_data(config, remaining_pixel_count, goal_pixel_count)


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
