import argparse
import os

from PIL import Image
from src.config import Config, load_config
from src.utils.graphing_utils import parse_filename_unix_time


def get_progress_images(
        config: Config
) -> tuple[int, list[Image.Image], list[int]]:
    """
    Get all the progress images and the timings between each image.

    :param config: The config for which to load the images.
    :return: A tuple of the total time between the first and last image; a
     list of all progress images; and a list of the time between each image.
     Note: the last list is one element shorter than the list of images.
    """
    # Get images and their timestamps
    images: list[Image.Image] = []
    timestamps: list[int] = []
    for filename in os.listdir(config.picture_dir):
        image_path = os.path.join(config.picture_dir, filename)
        image = Image.open(image_path)
        images.append(image)
        timestamps.append(
            parse_filename_unix_time(filename)
        )

    # Calculate distance between each image
    distances: list[int] = []
    for i in range(len(timestamps) - 1):
        # This list would be 1 shorter than the list of images.
        distances.append(timestamps[i + 1] - timestamps[i])
    # Add the last image's duration to the list, as average of all previous.
    average_duration = sum(distances) / len(distances)
    distances.append(int(average_duration * 2))  # average * 2 to signify end.

    total_time = timestamps[-1] - timestamps[0]
    return total_time, images, distances


def make_progress_gif(
        config_name: str,
        gif_length: int,
) -> None:
    config = load_config(config_name)
    total_time, images, distances = get_progress_images(config)
    if len(images) == 0:
        raise ValueError("No progress images found!")
    if total_time == 0:
        raise ValueError(
            "The time between the first and last image is 0 seconds, which "
            "means your gif would only be 1 frame!"
        )
    assert len(images) > 1 and len(distances) > 1, (
        f"Expected at least 2 images, but got {len(images)} images "
        f"and {len(distances)} distances!"
    )

    frame_multiplier = gif_length / total_time
    frame_durations: list[int] = []
    for distance in distances:
        frame_duration = distance * frame_multiplier * 1000  # in msec
        if frame_duration < 1:
            frame_duration = 1
        print(f"{int(frame_duration):>5}")
        frame_durations.append(int(frame_duration))

    output_path = os.path.join(config.output_dir,
                               config.paths.PROGRESS_GIF_NAME)
    images[0].save(
        output_path,
        append_images=images[1:],
        # interlace=False,
        # disposal=0,
        # transparency
        duration=frame_durations,
        loop=0,
    )


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(
        description="Make a gif of the progress pictures of a wplace canvas."
    )
    arg_parser.add_argument(
        "config",
        type=str,
        help="The config to use."
    )
    arg_parser.add_argument(
        "--gif_length",
        type=int,
        help="The length of the gif, in seconds."
    )

    args = arg_parser.parse_args()
    make_progress_gif(args.config, args.gif_length)
