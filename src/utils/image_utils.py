import typing

from PIL import Image

from src.utils.color_utils import (
    ColorTuple,
    ColorName,
    PIXEL_COLORS,
)


class Mask(Image.Image):
    def __init__(self, mask: Image.Image):
        super().__init__()
        self._from_image(mask)

    def _from_image(self, mask: Image.Image):
        # Largely copied from Image._new(); There still isn't a constructor
        #  for Image.Image that takes an image as argument. "FIXME" since 2010.
        self.im = mask.im
        self._mode = mask.mode
        self._size = mask.size
        self.info = mask.info.copy()

    # region Static constructors

    @staticmethod
    def new(size: tuple[int, int]) -> "Mask":
        return Mask(Image.new("1", size))

    @staticmethod
    def from_monochrome_image(img: Image.Image) -> "Mask":
        if img.mode != '1':
            raise ValueError("Mask must be monochrome!")
        return Mask(img)

    @staticmethod
    def from_pixel_opacity(img: Image.Image) -> "Mask":
        assert img.mode == 'RGBA', "Image must be RGBA!"
        mask = Image.new('1', img.size)
        for x in range(img.width):
            for y in range(img.height):
                pixel: ColorTuple = img.getpixel((x, y))  # type: ignore
                mask.putpixel((x, y), pixel[3])
        return Mask(mask)

    @staticmethod
    def from_image_difference(img1: Image.Image, img2: Image.Image) -> "Mask":
        """
        Create a mask from the difference between two images. White pixels
        are different, black pixels are the same.

        :param img1: First image to compare.
        :param img2: Second image to compare.
        :return: A new mask from the difference of two image, masking them
         as white.
        """
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
                    # Ignore transparent pixels: leave black.
                    continue
                if pixel1 != pixel2:
                    mask.putpixel((x, y), 1)  # White (1)
                else:
                    mask.putpixel((x, y), 0)  # Black (0)

        return Mask(mask)

    @staticmethod
    def from_image_color(img: Image.Image, color_name: ColorName) -> "Mask":
        if img.mode != 'RGBA':
            raise ValueError("Image must be RGBA!")
        color = PIXEL_COLORS[color_name]
        mask = Image.new('1', img.size)
        for x in range(img.width):
            for y in range(img.height):
                pixel: ColorTuple = img.getpixel((x, y))  # type: ignore
                mask_pixel = int(pixel == color)
                mask.putpixel((x, y), mask_pixel)
        return Mask(mask)

    # endregion Static constructors

    def get_inverted(self) -> "Mask":
        inverted_mask = Image.new('1', self.size)
        assert self.mode == '1', "Mask must be monochrome!"
        for x in range(self.width):
            for y in range(self.height):
                pixel: float = self.im.getpixel((x, y))  # type: ignore
                inverted_mask.putpixel((x, y), 1 - pixel)
        return Mask(inverted_mask)

    def invert(self) -> None:
        self._from_image(self.get_inverted())

    def union_lighter_color(self, other: "Mask") -> None:
        if self.size != other.size:
            raise ValueError("Masks must be the same size!")

        for x in range(self.width):
            for y in range(self.height):
                pixel: float = self.im.getpixel((x, y))
                other_pixel: float = other.im.getpixel((x, y))
                if pixel == other_pixel:
                    continue
                self.im.putpixel((x, y), max(pixel, other_pixel))

    def union_darker_color(self, other: "Mask") -> None:
        if self.size != other.size:
            raise ValueError("Masks must be the same size!")

        for x in range(self.width):
            for y in range(self.height):
                pixel: float = self.im.getpixel((x, y))
                other_pixel: float = other.im.getpixel((x, y))
                if pixel == other_pixel:
                    continue
                self.im.putpixel((x, y), min(pixel, other_pixel))

    def iterate_predicate(
            self,
            predicate: typing.Callable[[int], bool]
    ) -> typing.Generator[tuple[int, int], None, None]:
        """
        Create an iterator for the coordinates if the pixel at the coordinate
        passes the predicate.

        :return: A generator with pixel coordinates (x, y).
        """
        for x in range(self.width):
            for y in range(self.height):
                pixel: int = self.im.getpixel((x, y))
                if predicate(pixel):
                    yield x, y

    def count(self) -> dict[int, int]:
        count_data = {}
        for x in range(self.width):
            for y in range(self.height):
                pixel: int = self.im.getpixel((x, y))
                if pixel not in count_data:
                    count_data[pixel] = 0
                count_data[pixel] += 1
        return count_data


def get_remaining_pixels_image(
        template: Image.Image,
        progress: Image.Image,
) -> Image.Image:
    """
    Create an image for every color that doesn't match in the template
    and progress picture.

    :param template: The goal image, in case pixels are placed incorrectly.
    :param progress: The current state of the canvas, to get remaining pixels.
    :return: A new image built from the template but masked to the
     remaining pixels.
    """
    if template.size != progress.size:
        raise ValueError(
            f"Template and progress image were not the same size!\n"
            f"Template image: {template.size}, progress image: {progress.size}"
        )
    remaining_pixels = Image.new('RGBA', template.size, (0, 0, 0, 0))

    # Mask placed pixels to the template.
    placed_pixel_mask: Mask = Mask.from_pixel_opacity(progress)
    unplaced_pixel_mask: Mask = placed_pixel_mask.get_inverted()
    remaining_pixels.paste(template, mask=unplaced_pixel_mask)

    # Replace incorrect pixels with the template.
    incorrect_pixels = Mask.from_image_difference(template, progress)
    remaining_pixels.paste(template, mask=incorrect_pixels)

    return remaining_pixels


def get_pixel_count(img: Image.Image) -> dict[ColorName, int]:
    """
    Counts the occurence of each pixel in a given image.

    :param img: The image to count pixels for.
    :return: A dictionary mapping each color's name to its number of pixels.
    """
    assert img.mode == "RGBA", "Image is expected to be RGBA!"
    name_table: dict[ColorTuple, ColorName] = {
        v: k
        for k, v in PIXEL_COLORS.items()
    }
    pixel_count: dict[ColorName, int] = {k: 0 for k in name_table.values()}
    for x in range(img.width):
        for y in range(img.height):
            pixel: ColorTuple = img.getpixel((x, y))  # type: ignore
            pixel_name = name_table[pixel]
            pixel_count[pixel_name] += 1

    del pixel_count["Transparent"]
    sorted_pixel_count = dict(sorted(
        pixel_count.items(),
        key=lambda i: i[1],
        reverse=True
    ))
    return sorted_pixel_count


def filter_colors(
        img: Image.Image,
        colors: list[ColorName],
) -> Image.Image:
    """
    Mask colors in an image.

    :param img: Image to filter.
    :param colors: The colors to test for. If the image contains a color
     that isn't in this list, it will be made transparent in the output.
    :return: A new image where every color is either transparent or one
     of the given colors.
    """
    assert img.mode == "RGBA", "Image is expected to be RGBA!"
    filtered_colors: set[ColorTuple] = {PIXEL_COLORS[i] for i in colors}

    filtered_image = Image.new('RGBA', img.size, (0, 0, 0, 0))
    for x in range(img.width):
        for y in range(img.height):
            pixel: ColorTuple = img.getpixel((x, y))  # type: ignore
            if pixel in filtered_colors:
                filtered_image.putpixel((x, y), pixel)

    return filtered_image


def are_images_identical(
        img1: Image.Image,
        img2: Image.Image,
) -> bool:
    if img1.size != img2.size:
        return False

    for x in range(img1.width):
        for y in range(img1.height):
            pixel1 = img1.getpixel((x, y))
            pixel2 = img2.getpixel((x, y))
            if pixel1 != pixel2:
                return False
    return True
