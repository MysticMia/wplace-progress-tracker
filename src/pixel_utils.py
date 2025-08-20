from typing import Literal
from typing_extensions import NamedTuple


type ColorTuple = tuple[int, int, int, int]

type ColorName = Literal[
    'Black',
    'Dark Gray',
    'Gray',
    'Medium Gray',
    'Light Gray',
    'White',
    'Deep Red',
    'Dark Red',
    'Red',
    'Light Red',
    'Dark Orange',
    'Orange',
    'Gold',
    'Yellow',
    'Light Yellow',
    'Dark Goldenrod',
    'Goldenrod',
    'Light Goldenrod',
    'Dark Olive',
    'Olive',
    'Light Olive',
    'Dark Green',
    'Green',
    'Light Green',
    'Dark Teal',
    'Teal',
    'Light Teal',
    'Dark Cyan',
    'Cyan',
    'Light Cyan',
    'Dark Blue',
    'Blue',
    'Light Blue',
    'Dark Indigo',
    'Indigo',
    'Light Indigo',
    'Dark Slate Blue',
    'Slate Blue',
    'Light Slate Blue',
    'Dark Purple',
    'Purple',
    'Light Purple',
    'Dark Pink',
    'Pink',
    'Light Pink',
    'Dark Peach',
    'Peach',
    'Light Peach',
    'Dark Brown',
    'Brown',
    'Light Brown',
    'Dark Tan',
    'Tan',
    'Light Tan',
    'Dark Beige',
    'Beige',
    'Light Beige',
    'Dark Stone',
    'Stone',
    'Light Stone',
    'Dark Slate',
    'Slate',
    'Light Slate',
    'Transparent',
]


def get_pixel_colors() -> dict[ColorName, ColorTuple]:
    with open('src/wplace-colors.txt', 'r') as f:
        pixel_colors = {}
        for line in f:
            color_name, color_hex = line.split(" #")
            r = eval(f"0x{color_hex[:2]}")
            g = eval(f"0x{color_hex[2:4]}")
            b = eval(f"0x{color_hex[4:6]}")
            if color_name == "Transparent":
                color = (0, 0, 0, 0)
            else:
                color = (r, g, b, 1)
            pixel_colors[color_name] = color
    return pixel_colors


PIXEL_COLORS = get_pixel_colors()


class WplaceCoordinate(NamedTuple):
    TlX: int
    TlY: int
    PxX: int
    PxY: int

    def is_valid(self) -> bool:
        """
        Tests if a wplace coordinate is within certain bounds.

        :return: True if the coordinates are valid, else False.
        """
        return (
                0 <= self.TlX < 2048
                and 0 <= self.TlY < 2048
                and 0 <= self.PxX < 1000
                and 0 <= self.PxY < 1000
        )


def get_bottom_right_corner(
        top_left: WplaceCoordinate,
        size: tuple[int, int]
) -> WplaceCoordinate:
    """
    Use the top left corner and the image size to calculate the
    bottom right corner.

    :return: A new wplace coordinate for the bottom right corner.
    """
    new_x = top_left.PxX + size[0] - 1
    new_y = top_left.PxY + size[1] - 1
    coords = WplaceCoordinate(
        top_left.TlX + new_x // 1000,
        top_left.TlY + new_y // 1000,
        new_x % 1000,
        new_y % 1000,
        )
    assert coords.is_valid(), coords
    # assert coords == WplaceCoordinate(988, 1414, 798, 37), coords
    return coords
