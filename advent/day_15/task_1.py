import functools
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, NamedTuple

import click
import more_itertools as mit
import tqdm

from ..io_utils import get_stripped_lines
from ..logs import setup_logging

logger = logging.getLogger(__name__)


class Position(NamedTuple):
    y: int
    x: int


def manhattan_distance(a: Position, b: Position) -> int:
    return abs(a.y - b.y) + abs(a.x - b.x)


@dataclass
class Sensor:
    position: Position
    beacon: Position

    @functools.cached_property
    def r(self) -> int:
        return manhattan_distance(self.position, self.beacon)


# regexp pattern to match 'Sensor at x=2, y=18: closest beacon is at x=-2, y=15'
pattern = re.compile(
    r"^Sensor at x=(?P<sensor_x>\-?\d+), y=(?P<sensor_y>\-?\d+)\: "
    r"closest beacon is at x=(?P<beacon_x>\-?\d+), y=(?P<beacon_y>\-?\d+)"
)


def parse_sensors(filename: Path) -> Iterable[Sensor]:
    for line in get_stripped_lines(filename):
        match = pattern.match(line)
        assert match is not None
        yield Sensor(
            position=Position(int(match["sensor_y"]), int(match["sensor_x"])),
            beacon=Position(int(match["beacon_y"]), int(match["beacon_x"])),
        )


EMPTY = 0
SENSOR = 1
BEACON = 2
RANGE = 3


def get_highest_distance_between_sensor_and_beacon(sensors: Iterable[Sensor]) -> int:
    return max(
        abs(sensor.position.y - sensor.beacon.y)
        + abs(sensor.position.x - sensor.beacon.x)
        for sensor in sensors
    )


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
@click.argument("target_y", type=int, required=True)
def main(filename: Path, target_y: int) -> None:
    sensors = list(parse_sensors(filename))

    highest_distance_between_sensor_and_beacon = (
        get_highest_distance_between_sensor_and_beacon(sensors)
    )
    logger.debug(
        "Highest distance between sensor and beacon: %d",
        highest_distance_between_sensor_and_beacon,
    )

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
        if not can_have_beacon(sensors, point):
            points_in_range += 1

    click.echo(str(points_in_range))


def can_have_beacon(sensors: Iterable[Sensor], point: Position) -> bool:
    for sensor in sensors:
        if manhattan_distance(sensor.position, point) <= sensor.r:
            return False
    return True


if __name__ == "__main__":
    setup_logging()
    main()
