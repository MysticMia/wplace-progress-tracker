import json
import os.path
import typing
from PIL import Image

from src.utils.color_utils import (
    ColorName,
    PIXEL_COLORS,
    FREE_PIXEL_COLORS,
    ColorTuple,
    PREMIUM_PIXEL_COLORS,
)
from src.utils.coord_utils import (
    WplaceCoordinate,
    get_bottom_right_corner,
)
from typing import TypedDict

__all__ = [
    "Config",
    "load_config"
]


CONFIG_DIRECTORY = "configs"

TopLeftCorner = TypedDict(
    "TopLeftCorner",
    {
        "Tl X": int,
        "Tl Y": int,
        "Px X": int,
        "Px Y": int
    }
)


class InvalidColorNameError(ValueError):
    pass


class ImageSize(TypedDict):
    width: int
    height: int


class Subdirectories(TypedDict):
    picture: str
    output: str


class ConfigFile(TypedDict):
    top_left: TopLeftCorner
    image_size: ImageSize
    data_directory: str
    subdirectories: Subdirectories
    bought_colors: list[str]


def _validate_colors(color_names: list[str]) -> list[ColorName]:
    invalid_names: list[str] = []
    for color_name in color_names:
        if color_name not in typing.get_args(ColorName.__value__):
            invalid_names.append(f"'{color_name}'")
    if len(invalid_names) > 0:
        raise InvalidColorNameError(
            f"Invalid color names: "
            + ', '.join(invalid_names)
        )
    return typing.cast(list[ColorName], color_names)


class FileNames:
    TEMPLATE_NAME = "template.png"
    GRAPH_NAME = "graph.png"
    REMAINING_PIXELS_NAME = "remaining_pixels.png"
    REMAINING_PLACEABLE_PIXELS_NAME = "remaining_pixels_placeable.png"
    REMAINING_UNPLACEABLE_PIXELS_NAME = "remaining_pixels_unplaceable.png"
    CIRCLE_OVERLAY_NAME = "pixel_finder.png"
    REMAINING_PIXEL_COUNT_NAME = "remaining_pixels.txt"
    PROGRESS_GIF_NAME = "progress.gif"
    AVERAGE_PIXEL_PLACEMENT_GRAPH_NAME = "average_placement_graph.png"
    PIXEL_PROGRESS_GRAPH_NAME = "progress_graph.png"
    MISPLACEMENT_GRAPH_NAME = "misplacement_graph.png"


class Config:
    name: str
    paths = FileNames()
    top_left: WplaceCoordinate
    image_size: tuple[int, int]
    data_directory: str
    subdirectories: Subdirectories
    bought_colors: list[ColorName]

    def __init__(self, name: str, config_data: ConfigFile) -> None:
        self.name = name
        self.top_left = WplaceCoordinate(
            config_data["top_left"]["Tl X"],
            config_data["top_left"]["Tl Y"],
            config_data["top_left"]["Px X"],
            config_data["top_left"]["Px Y"]
        )
        self.image_size = (
            config_data["image_size"]["width"],
            config_data["image_size"]["height"]
        )
        if self.image_size[0] < 1 or self.image_size[1] < 1:
            raise ValueError("Image size must be greater than 0!")

        self.data_directory = config_data["data_directory"]
        self.subdirectories = config_data["subdirectories"]
        for subdirectory in Subdirectories.__annotations__:
            if subdirectory not in self.subdirectories:
                raise KeyError(subdirectory)
        self.bought_colors = _validate_colors(config_data["bought_colors"])

        self.create_directories()

    def create_directories(self) -> None:
        os.makedirs(self.picture_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

    def get_template_image(self):
        template_path = os.path.join(self.data_directory,
                                     self.paths.TEMPLATE_NAME)
        if not os.path.exists(template_path):
            raise FileNotFoundError(
                f"Template image not found! Please add "
                f"{self.paths.TEMPLATE_NAME} to the picture directory "
                f"(path: {template_path})."
            )
        return Image.open(template_path).convert("RGBA")

    # region Properties
    @property
    def bottom_right(self):
        return get_bottom_right_corner(self.top_left, self.image_size)

    @property
    def picture_dir(self):
        return os.path.join(
            self.data_directory,
            self.subdirectories["picture"]
        )

    @property
    def output_dir(self):
        return os.path.join(
            self.data_directory,
            self.subdirectories["output"]
        )

    @property
    def available_colors(self) -> dict[ColorName, ColorTuple]:
        """
        Get a dictionary of colors that can be placed by the user.

        :return: A PIXEL_COLORS dictionary where every key is either
         a free color or bought color.
        """
        return {
            color_name: PIXEL_COLORS[color_name]
            for color_name in list(FREE_PIXEL_COLORS) + self.bought_colors
        }

    @property
    def unavailable_colors(self) -> dict[ColorName, ColorTuple]:
        """
        Get a dictionary of colors that cannot be placed by the user.

        :return: A PIXEL_COLORS dictionary where every key is a premium
         color that has not been bought.
        """
        return {
            color_name: PREMIUM_PIXEL_COLORS[color_name]
            for color_name in (
                    set(PREMIUM_PIXEL_COLORS)
                    - set(self.bought_colors)
            )
        }

    # endregion Properties


def load_config(name: str) -> Config:
    path = os.path.join(CONFIG_DIRECTORY, f"{name}.json")
    if not os.path.exists(path):
        raise ValueError(
            f"Config file not found! Please create a `{name}.json` file in "
            f"the `{CONFIG_DIRECTORY}` directory with the required keys "
            f"to use this config name!"
        ) from None

    with open(path, "r") as f:
        config_data: ConfigFile = json.loads(f.read())

    try:
        return Config(name, config_data)
    except KeyError as ex:
        missing_keys = ', '.join(ex.args)
        raise ValueError(
            f"Your config file is missing the key(s): {missing_keys}! "
            "Please check example.json for the latest format!"
        ) from None
