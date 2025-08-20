import json
import os.path
from .pixel_utils import WplaceCoordinate, get_bottom_right_corner
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


class ImageSize(TypedDict):
    width: int
    height: int


class Subdirectories(TypedDict):
    picture: str
    progress: str


class ConfigFile(TypedDict):
    top_left: TopLeftCorner
    image_size: ImageSize
    data_directory: str
    subdirectories: Subdirectories


class Config:
    name: str
    top_left: WplaceCoordinate
    image_size: tuple[int, int]
    data_directory: str
    subdirectories: Subdirectories

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

        self.create_directories()

    def create_directories(self) -> None:
        os.makedirs(self.picture_dir, exist_ok=True)
        os.makedirs(self.progress_dir, exist_ok=True)

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
    def progress_dir(self):
        return os.path.join(
            self.data_directory,
            self.subdirectories["progress"]
        )


def load_config(name: str) -> Config:
    path = os.path.join(CONFIG_DIRECTORY, f"{name}.json")
    if not os.path.exists(path):
        raise ValueError(
            f"Config file not found! Please create a {name}.json file in "
            f"the `{CONFIG_DIRECTORY}` directory with the required keys "
            f"to use this config name!"
        )

    with open(path, "r") as f:
        config_data: ConfigFile = json.loads(f.read())

    return Config(name, config_data)
