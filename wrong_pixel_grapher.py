import argparse
from PIL import Image
from src.config import load_config, Config

from src.utils.color_utils import ColorName
from src.utils.graphing_utils import Grapher
from src.utils.image_utils import Mask, get_pixel_count
import os


def _get_image_misplacement_count(
        template: Image.Image,
        img: Image.Image,
) -> dict[ColorName, int]:
    mask: Mask = Mask.from_image_difference(template, img)
    wrong_pixels = Image.new("RGBA", template.size, (0, 0, 0, 0))
    wrong_pixels.paste(template, mask=mask)
    return get_pixel_count(wrong_pixels)


def put_misplacement_data(
        config: Config,
        grapher: Grapher,
) -> None:
    template: Image.Image = config.get_template_image()
    for image_name in os.listdir(config.picture_dir):
        assert image_name.endswith(".png"), (
            f"Expected .png file, got {image_name}!"
        )
        path = os.path.join(config.picture_dir, image_name)
        img = Image.open(path)
        image_data = _get_image_misplacement_count(template, img)
        grapher.add_data_point_from_filename(image_name, image_data)


def save_misplacement_data(
        config_name: str,
        max_minutes: int | None = None,
        step_graph: bool = False,
):
    config = load_config(config_name)
    grapher = Grapher()
    put_misplacement_data(config, grapher)
    grapher.make_graph(
        config,
        config.paths.MISPLACEMENT_GRAPH_NAME,
        f"Misplaced pixels on '{config.name}'",
        "Misplaced pixels",
        max_minutes=max_minutes,
        as_step=step_graph,
    )


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        description="Make a graph of the change of incorrect pixels over time."
    )
    arg_parser.add_argument(
        "config",
        type=str,
        help="The config to use."
    )

    arg_parser.add_argument(
        "--max_minutes",
        type=int,
        default=None,
        help="How far back in time to make the graph, in minutes. "
             "(Default: No limit)"
    )
    arg_parser.add_argument(
        "--step_graph",
        action="store_true",
        help="Whether to make the graph as steps or as a line. "
             "(Default: Line graph)"
    )

    args = arg_parser.parse_args()

    save_misplacement_data(
        args.config,
        args.max_minutes,
        args.step_graph,
    )
