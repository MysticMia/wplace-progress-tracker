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
    x = abs(
        1000 * (top_left.TlX - bottom_right.TlX)
        + top_left.PxX - bottom_right.PxX
        + 1  # size is inclusive
    )
    y = abs(
        1000 * (top_left.TlY - bottom_right.TlY)
        + top_left.PxY - bottom_right.PxY
        + 1  # size is inclusive
    )
    return x, y
