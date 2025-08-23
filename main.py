import argparse

from src import (
    save_latest_image,
    save_progress_image,
    save_pixel_count,
    save_pixel_progress_graph,
)


def main(
        config_name: str,
        max_minutes: int | None,
        reload_only: bool
):
    if not reload_only:
        print("Fetching progress image...")
        timestamp: str = save_latest_image(config_name)
        print("Creating remainder image...")
        save_progress_image(config_name, f"{timestamp}.png")
        print("Counting pixels...")
        save_pixel_count(config_name, timestamp)
    print("Generating pixel progress graph...")
    save_pixel_progress_graph(config_name, max_minutes)
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

    arg_parser.add_argument(
        "--max_minutes",
        type=int,
        default=None,
        help="How far back in time to make the graph, in minutes."
    )
    arg_parser.add_argument(
        "--reload_only",
        action="store_true",
        help="Whether to refetch an image or only reload the graph."
    )

    args = arg_parser.parse_args()

    main(args.config, args.max_minutes, args.reload_only)
