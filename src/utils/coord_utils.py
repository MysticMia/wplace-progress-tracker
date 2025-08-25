from typing_extensions import NamedTuple


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
    new_x = top_left.PxX + size[0] - 1  # size is inclusive
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


def get_canvas_size(
        top_left: WplaceCoordinate,
        bottom_right: WplaceCoordinate,
) -> tuple[int, int]:
    """
    Calculate the width and height of an area between two corners.

    :param top_left: The top left corner of the selection.
    :param bottom_right: The bottom right corner of the selection.
    :return: A tuple of the width (x) and height (y) of the selected area.
    """
    x = (
        1000 * (bottom_right.TlX - top_left.TlX)
        + bottom_right.PxX - top_left.PxX
        + 1  # size is inclusive
    )
    y = (
        1000 * (bottom_right.TlY - top_left.TlY)
        + bottom_right.PxY - top_left.PxY
        + 1  # size is inclusive
    )
    return x, y


def pixel_string_to_coordinate(pixel_string: str) -> WplaceCoordinate:
    # (Tl X: 1037, Tl Y: 1397, Px X: 791, Px Y: 234)
    # to WplaceCoordinate(1037, 1397, 791, 234)
    pixel_string = (pixel_string
                    .replace("(", "")
                    .replace(")", "")
                    .strip())
    sections = pixel_string.split(",")
    assert len(sections) == 4
    num_strings = [section.split(": ")[1] for section in sections]
    nums = [int(num_string) for num_string in num_strings]
    assert len(nums) == 4
    return WplaceCoordinate(nums[0], nums[1], nums[2], nums[3])
