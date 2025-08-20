import argparse

from src import (
    save_latest_image,
    save_progress_image,
    save_pixel_count,
    save_pixel_progress_graph,
)


def main(config_name: str):
    print("Fetching progress image...")
    timestamp: str = save_latest_image(config_name)
    print("Creating remainder image...")
    save_progress_image(config_name, f"{timestamp}.png")
    print("Counting pixels...")
    save_pixel_count(config_name, timestamp)
    print("Generating pixel progress graph...")
    save_pixel_progress_graph(config_name)
    print("Successfully created progress graph.")


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        description="Load the latest wplace image and update a progress graph."
    )
    arg_parser.add_argument(
        "config",
        type=str,
        help="The config to use."
    )

    args = arg_parser.parse_args()

    main(args.config)
