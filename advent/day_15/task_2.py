import logging
import re
from pathlib import Path
from typing import Iterable, NamedTuple

import click
import more_itertools as mit
import tqdm

from ..logs import setup_logging
from .task_1 import get_highest_distance_between_sensor_and_beacon, parse_sensors

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

    for x in range(max_x + 1):
        pass

    def get_sensor_and_beacon_positions() -> Iterable[Position]:
        for sensor in sensors:
            yield sensor.position
            yield sensor.beacon

    min_x, max_x = mit.minmax(map(lambda p: p.x, get_sensor_and_beacon_positions()))
    min_y, max_y = mit.minmax(map(lambda p: p.y, get_sensor_and_beacon_positions()))
    min_x -= highest_distance_between_sensor_and_beacon
    max_x += highest_distance_between_sensor_and_beacon
    min_y -= highest_distance_between_sensor_and_beacon
    max_y += highest_distance_between_sensor_and_beacon

    points_in_range = 0
    for x in tqdm.trange(min_x, max_x + 1):
        point = Position(y=target_y, x=x)
        for sensor in sensors:
            if point == sensor.beacon:
                break  # there is a beacon there already
            r = manhattan_distance(sensor.position, sensor.beacon)
            if manhattan_distance(sensor.position, point) <= r:
                points_in_range += 1
                break

    click.echo(str(points_in_range))


if __name__ == "__main__":
    setup_logging()
    main()
