import argparse
import os.path

from src import (
    save_latest_image,
    save_remainder_images,
    save_pixel_count,
    save_pixel_progress_graph,
)
from src.config import load_config


def main(
        config_names: list[str],
        ignore_if_identical: bool,
):
    for config_name in config_names:
        config = load_config(config_name)
        print(f"Fetching for `{config_name}`...")
        timestamp: str | None = save_latest_image(config, ignore_if_identical)
        if timestamp is None:
            assert ignore_if_identical
            # ^ `ignore_if_identical` must be true for `timestamp` to be None.
            print("The canvas hasn't changed! Discarding downloaded image.\n")
            continue

        progress_path = os.path.join(config.picture_dir,
                                     timestamp + ".png")
        print(f"Added latest image at `{progress_path}`")
        save_remainder_images(config, f"{timestamp}.png")
        remainder_path = os.path.join(config.output_dir,
                                      config.paths.REMAINING_PIXELS_NAME)
        print(f"Updated remainder pictures at `{remainder_path}`")
        save_pixel_count(config)
        count_path = os.path.join(config.output_dir,
                                  config.paths.REMAINING_PIXEL_COUNT_NAME)
        print(f"Updated pixel count at `{count_path}`\n")
    print("Successfully fetched latest image(s)!")


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        description="Load the latest wplace image and update a progress graph."
    )
    arg_parser.add_argument(
        "config",
        type=str,
        nargs="+",
        help="The config to use."
    )
    arg_parser.add_argument(
        "--ignore_if_identical",
        action="store_true",
        help="Discard the downloaded image if it is identical to the most "
             "recent already-saved image."
    )
    args = arg_parser.parse_args()

    main(args.config, args.ignore_if_identical)
