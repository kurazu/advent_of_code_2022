import logging
import re
from pathlib import Path
from typing import Iterable, NamedTuple

import click
import more_itertools as mit
import tqdm

from ..logs import setup_logging
from .task_1 import (
    Position,
    can_have_beacon,
    get_highest_distance_between_sensor_and_beacon,
    parse_sensors,
)

logger = logging.getLogger(__name__)


@click.command()
@click.argument(
    "filename",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        path_type=Path,
    ),
    required=True,
)
@click.argument("max_x", type=int, required=True)
@click.argument("max_y", type=int, required=True)
def main(filename: Path, max_x: int, max_y: int) -> None:
    sensors = list(parse_sensors(filename))

    highest_distance_between_sensor_and_beacon = (
        get_highest_distance_between_sensor_and_beacon(sensors)
    )
    logger.debug(
        "Highest distance between sensor and beacon: %d",
        highest_distance_between_sensor_and_beacon,
    )

    for y in tqdm.trange(max_y + 1, desc="y"):
        for x in tqdm.trange(max_x + 1, desc="x"):
            point = Position(y=y, x=x)
            if can_have_beacon(sensors, point):
                logger.debug("Point %s can have a beacon", point)
                click.echo(str(point.x * 4000000 + point.y))
                return
    raise AssertionError()


if __name__ == "__main__":
    setup_logging()
    main()
