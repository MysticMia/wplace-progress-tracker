from typing import Literal


__all__ = [
    "ColorTuple",
    "ColorName",
    "PIXEL_COLORS",
    "FREE_PIXEL_COLORS",
    "PREMIUM_PIXEL_COLORS",
]


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
                color = (r, g, b, 255)
            pixel_colors[color_name] = color
    return pixel_colors


PIXEL_COLORS: dict[ColorName, ColorTuple] = get_pixel_colors()


free_pixel_color_names: set[ColorName] = {
    "Black",
    "Dark Gray",
    "Gray",
    "Light Gray",
    "White",
    "Deep Red",
    "Red",
    "Orange",
    "Gold",
    "Yellow",
    "Light Yellow",
    "Dark Green",
    "Green",
    "Light Green",
    "Dark Teal",
    "Teal",
    "Light Teal",
    "Cyan",
    "Dark Blue",
    "Blue",
    "Indigo",
    "Light Indigo",
    "Dark Purple",
    "Purple",
    "Light Purple",
    "Dark Pink",
    "Pink",
    "Light Pink",
    "Dark Brown",
    "Brown",
    "Beige",
    "Transparent"
}


FREE_PIXEL_COLORS: dict[ColorName, ColorTuple] = {
    name: tup
    for name, tup in PIXEL_COLORS.items()
    if name in free_pixel_color_names
}


PREMIUM_PIXEL_COLORS: dict[ColorName, ColorTuple] = {
    name: tup
    for name, tup in PIXEL_COLORS.items()
    if name not in free_pixel_color_names
}
