import argparse
import os.path
from PIL import Image
from .config import load_config, Config
from .pixel_utils import ColorTuple

TEMPLATE_NAME = "template.png"
REMAINING_PIXELS_NAME = "remaining_pixels.png"


def get_difference_mask(
        img1: Image.Image,
        img2: Image.Image,
) -> Image.Image:
    if img1.size != img2.size:
        raise ValueError("Images must be the same size")
    assert img1.mode == 'RGBA', "Image 1 must be RGBA!"
    assert img2.mode == 'RGBA', "Image 2 must be RGBA!"

    mask = Image.new('1', img1.size)  # '1' = black and white

    # Iterate through each pixel.
    for x in range(img1.width):
        for y in range(img1.height):
            pixel1: ColorTuple = img1.getpixel((x, y))  # type: ignore
            pixel2: ColorTuple = img2.getpixel((x, y))  # type: ignore
            if pixel1[3] == 0 or pixel2[3] == 0:
                # Ignore transparent pixels.
                continue
            if pixel1 != pixel2:
                mask.putpixel((x, y), 1)  # White (1)
            else:
                mask.putpixel((x, y), 0)  # Black (0)

    return mask


def simple_mask_from_image(img: Image.Image) -> Image.Image:
    assert img.mode == 'RGBA', "Image must be RGBA!"
    mask = Image.new('1', img.size)
    for x in range(img.width):
        for y in range(img.height):
            pixel: ColorTuple = img.getpixel((x, y))  # type: ignore
            if pixel[3] == 0:
                mask.putpixel((x, y), 0)
            else:
                mask.putpixel((x, y), 1)
    return mask


def invert_mask(mask: Image.Image) -> Image.Image:
    inverted_mask = Image.new('1', mask.size)
    assert mask.mode == '1', "Mask must be monochrome!"
    for x in range(mask.width):
        for y in range(mask.height):
            pixel: float = mask.getpixel((x, y))  # type: ignore
            inverted_mask.putpixel((x, y), 1 - pixel)
    return inverted_mask


def get_remaining_pixels(
        template: Image.Image,
        progress: Image.Image,
) -> Image.Image:
    remaining_pixels = Image.new('RGBA', template.size, (0, 0, 0, 0))

    # Add all pixels that are transparent.
    placed_pixel_mask = simple_mask_from_image(progress)
    unplaced_pixel_mask = invert_mask(placed_pixel_mask)
    remaining_pixels.paste(template, mask=unplaced_pixel_mask)

    # Add incorrect pixels, since those still need to be correctly placed.
    incorrect_pixels = get_difference_mask(template, progress)
    remaining_pixels.paste(template, mask=incorrect_pixels)

    return remaining_pixels


def load_images(config: Config, progress_picture_name: str):
    template_path = os.path.join(config.picture_dir, TEMPLATE_NAME)
    progress_path = os.path.join(config.picture_dir, progress_picture_name)

    if not os.path.exists(template_path):
        raise FileNotFoundError(
            f"Template image not found! Please add {TEMPLATE_NAME} to the "
            f"picture directory (path: {template_path})."
        )
    if not os.path.exists(progress_path):
        raise FileNotFoundError(
            f"Progress image not found! Please add {progress_picture_name} "
            f"to the picture directory (path: {progress_path})."
        )
    template = Image.open(template_path).convert("RGBA")
    image2 = Image.open(progress_path).convert("RGBA")
    return template, image2


def main(config_name: str, progress_picture_name: str):
    config = load_config(config_name)

    template, image2 = load_images(config, progress_picture_name)
    remainder_img = get_remaining_pixels(template, image2)

    path = os.path.join(config.data_directory, REMAINING_PIXELS_NAME)
    remainder_img.save(path)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        description="Get the remaining pixels using the template and a "
                    "progress image."
    )
    arg_parser.add_argument(
        "config",
        type=str,
        help="The config to use for the template."
    )
    arg_parser.add_argument(
        "progress_picture_name",
        type=str,
        help="The progress picture name to compare to."
    )

    args = arg_parser.parse_args()
    main(args.config, args.progress_picture_name)
