import argparse

from src import (
    save_latest_image,
    save_progress_image,
    save_pixel_count,
    save_pixel_progress_graph,
)


def main(
        config_names: list[str],
):
    for config_name in config_names:
        print(f"Fetching latest image for {config_name}...")
        timestamp: str = save_latest_image(config_name)
        print("Creating remainder image...")
        save_progress_image(config_name, f"{timestamp}.png")
        print("Counting pixels...")
        save_pixel_count(config_name)
        print()
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
    args = arg_parser.parse_args()

    main(args.config)
