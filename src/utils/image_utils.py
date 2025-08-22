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
    def from_monochrome_image(img: Image.Image):
        if img.mode != '1':
            raise ValueError("Mask must be monochrome!")
        return Mask(img)

    @staticmethod
    def from_pixel_opacity(img: Image.Image):
        assert img.mode == 'RGBA', "Image must be RGBA!"
        mask = Image.new('1', img.size)
        for x in range(img.width):
            for y in range(img.height):
                pixel: ColorTuple = img.getpixel((x, y))  # type: ignore
                mask.putpixel((x, y), pixel[3])
        return Mask(mask)

    @staticmethod
    def from_image_difference(img1: Image.Image, img2: Image.Image):
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


def get_remaining_pixels(
        template: Image.Image,
        progress: Image.Image,
) -> Image.Image:
    remaining_pixels = Image.new('RGBA', template.size, (0, 0, 0, 0))

    # Add all pixels that are transparent.
    placed_pixel_mask: Mask = Mask.from_pixel_opacity(progress)
    unplaced_pixel_mask: Mask = placed_pixel_mask.get_inverted()
    remaining_pixels.paste(template, mask=unplaced_pixel_mask)

    # Add incorrect pixels, since those still need to be correctly placed.
    incorrect_pixels = Mask.from_image_difference(template, progress)
    remaining_pixels.paste(template, mask=incorrect_pixels)

    return remaining_pixels


def get_pixel_count(img: Image.Image) -> dict[ColorName, int]:
    assert img.mode == "RGBA", "Image is expected to be RGBA!"
    name_table: dict[ColorTuple, ColorName] = {
        v: k
        for k, v in PIXEL_COLORS.items()
    }
    pixel_count: dict[ColorName, int] = {k: 0 for k in name_table.values()}
    for x in range(img.width):
        for y in range(img.height):
            pixel: ColorTuple = img.getpixel((x, y))  # type: ignore
            pixel = (pixel[0], pixel[1], pixel[2], pixel[3]//255)
            pixel_name = name_table[pixel]
            pixel_count[pixel_name] += 1

    del pixel_count["Transparent"]
    sorted_pixel_count = dict(sorted(
        pixel_count.items(),
        key=lambda i: i[1],
        reverse=True
    ))
    return sorted_pixel_count
