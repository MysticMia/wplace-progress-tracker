import argparse
import asyncio
import aiohttp
import os
from datetime import datetime
from io import BytesIO
from math import ceil
from PIL import Image

from src.config import load_config, Config
from src.utils.coord_utils import WplaceCoordinate
from src.utils.image_utils import are_images_identical

TIMESTAMP = datetime.now().strftime("%Y-%m-%dT%H%M%S")
FILE_NAME = f"{TIMESTAMP}.png"

CHUNK_SIZES = (1000, 1000)
API_FORMAT = "https://backend.wplace.live/files/s0/tiles/{}/{}.png"


def get_grid_coordinates(
        top_left: WplaceCoordinate,
        image_size: tuple[int, int]
) -> list[tuple[int, int]]:
    """
    Helper to calculate what chunks the image intersects.

    :return: A list of chunk (x,y) coordinates.
    """
    x_chunk_count: int = ceil((top_left.PxX + image_size[0]) / 1000)
    y_chunk_count: int = ceil((top_left.PxY + image_size[1]) / 1000)
    chunks = []
    for x in range(0, x_chunk_count):
        for y in range(0, y_chunk_count):
            chunks.append((top_left.TlX + x, top_left.TlY + y))
    return chunks


async def fetch_picture(
        session: aiohttp.ClientSession,
        tl_x: int,
        tl_y: int,
) -> bytes:
    """
    Fetch a picture from the wplace API.

    :param session: The session to use for the request.
    :param tl_x: The x coordinate of the chunk to fetch.
    :param tl_y: The y coordinate of the chunk to fetch.
    :return: A byte string containing the image data.
    """
    async with session.get(
            API_FORMAT.format(tl_x, tl_y)
    ) as api_response:
        image_data = await api_response.read()
        if api_response.status == 404:
            print(
                f"{api_response.status}: Failed to fetch chunk {tl_x},{tl_y}\n"
                f"This can be because the chunk is entirely empty."
            )
            image_byte_io = BytesIO()
            empty_image = Image.new("RGBA", CHUNK_SIZES, color=(0, 0, 0, 0))
            empty_image.save(image_byte_io, format="PNG")
            image_byte_io.seek(0)
            image_data = image_byte_io.getvalue()
        elif api_response.status != 200:
            raise ValueError(
                f"{api_response.status}: Failed to fetch chunk {tl_x},{tl_y}"
            )
        return image_data


async def fetch_pictures(coords: list[tuple[int, int]]) -> list[bytes]:
    """
    Helper to fetch all chunk images in parallel.

    :param coords: The coordinates of the chunk images to fetch.
    :return: A list of image byte strings, corresponding to the
     input coordinates.
    """
    headers = {
        "User-Agent": "Python Wplace progress canvas creator by "
                      "MysticMia (github)"
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        image_queries = []
        for coord in coords:
            image_queries.append(
                fetch_picture(session, coord[0], coord[1])
            )
        return await asyncio.gather(*image_queries)


def stitch_pictures(
        coords: list[tuple[int, int]],
        images: list[bytes]
) -> Image.Image:
    """
    Stitch the chunk images into a single image, depending on their
    chunk coordinates.

    :param coords: The coordinates of each image's chunk.
    :param images: The byte strings containing the image data.
    :return: The stitched image.
    """
    x_size, y_size = [len(set(i)) for i in zip(*coords)]
    assert x_size * y_size == len(coords)
    canvas = Image.new(
        "RGBA",
        (x_size * CHUNK_SIZES[0],
         y_size * CHUNK_SIZES[1]),
        color=(0, 0, 0, 0)
    )

    top_left = coords[0]
    for coord, image_bytes in zip(coords, images):
        # Remove world-space chunk offset
        coord = (coord[0] - top_left[0],
                 coord[1] - top_left[1])
        # Expand chunks to their be their chunk sizes
        coord = (coord[0] * CHUNK_SIZES[0],
                 coord[1] * CHUNK_SIZES[1])
        img = Image.open(BytesIO(image_bytes))
        canvas.paste(img, coord)
    return canvas


def get_canvas_position(
        coord: WplaceCoordinate,
        *,
        top_left: WplaceCoordinate
) -> tuple[int, int]:
    """
    Helper to convert a wplace coordinate to a relative canvas position.
    :param coord: The wplace coordinate to convert to a canvas position.
    :param top_left: The top left corner of the wplace image.
    :return: A relative canvas position.
    """
    chunk_x = coord.TlX - top_left.TlX
    chunk_y = coord.TlY - top_left.TlY
    x = chunk_x * 1000 + coord.PxX
    y = chunk_y * 1000 + coord.PxY
    return x, y


def crop_image(
        image: Image.Image,
        top_left: WplaceCoordinate,
        bottom_right: WplaceCoordinate,
):
    """
    Crop an image

    :param image: The (stitched) image to crop.
    :param top_left: The top left corner of the wplace image.
    :param bottom_right: The bottom right corner of the wplace image.
    :return: The cropped image.
    """
    # The top left corner is always in 0, 0:
    # At any point, the top left corner will be in the relative top left chunk.
    # To get the canvas position, the inner chunk coordinates are subtracted,
    #  and for top left, that means
    x1, y1 = get_canvas_position(top_left, top_left=top_left)
    x2, y2 = get_canvas_position(bottom_right, top_left=top_left)
    return image.crop((
        x1,
        y1,
        x2 + 1,  # cropping is inclusive
        y2 + 1,
    ))


def get_latest_progress_picture(config: Config):
    pictures = os.listdir(config.picture_dir)
    if len(pictures) == 0:
        return None
    image_name = sorted(pictures)[-1]  # latest timestamp
    image_path = os.path.join(config.picture_dir, image_name)
    return Image.open(image_path)


def save_latest_image(
        config: Config,
        ignore_if_identical: bool,
) -> str | None:
    """
    Fetch and save the most recent wplace canvas image.

    :param config: The config for which to get the canvas.
    :param ignore_if_identical: Don't create a file if the downloaded image is
     identical to the most recent saved one.
    :return: The timestamp of the saved image (the current time), or None if
     **ignore-if_identical** is True and the canvas hasn't changed.
    """
    coords = get_grid_coordinates(config.top_left, config.image_size)

    # Get image
    pictures = asyncio.run(fetch_pictures(coords))
    chunk_picture = stitch_pictures(coords, pictures)
    image = crop_image(chunk_picture, config.top_left, config.bottom_right)

    # Compare image
    if ignore_if_identical:
        latest_image = get_latest_progress_picture(config)
        if (
                latest_image is not None
                and are_images_identical(image, latest_image)
        ):
            return None

    # Save image
    path = os.path.join(config.picture_dir, FILE_NAME)
    image.save(path)
    return TIMESTAMP


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        description="Fetch the latest wplace image and save it."
    )
    arg_parser.add_argument(
        "config",
        type=str,
        help="The config to use and fetch for."
    )

    args = arg_parser.parse_args()

    t = save_latest_image(
        load_config(args.config),
        args.ignore_if_identical
    )
    print(f"Created progress picture at {t}.png")
