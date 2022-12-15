import itertools as it
import logging
import re
from pathlib import Path
from typing import Iterable, NamedTuple

import click
import more_itertools as mit
import numpy as np
from numpy import typing as npt

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines
from ..logs import setup_logging

logger = logging.getLogger(__name__)


class Position(NamedTuple):
    y: int
    x: int


class Sensor(NamedTuple):
    position: Position
    beacon: Position


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
def main(filename: Path, target_y: int) -> str:
    sensors = list(parse_sensors(filename))

    highest_distance_between_sensor_and_beacon = max(
        abs(sensor.position.y - sensor.beacon.y)
        + abs(sensor.position.x - sensor.beacon.x)
        for sensor in sensors
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

    logger.debug(
        "Highest distance between sensor and beacon: %d",
        highest_distance_between_sensor_and_beacon,
    )
    width = max_x - min_x + 1
    height = max_y - min_y + 1
    logger.debug("Creating board of size %d x %d", width, height)
    breakpoint()
    board = np.zeros((height, width), dtype=np.uint8)
    for sensor in sensors:
        r = abs(sensor.position.y - sensor.beacon.y) + abs(
            sensor.position.x - sensor.beacon.x
        )
        for y in range(sensor.position.y - r, sensor.position.y + r + 1):
            for x in range(sensor.position.x - r, sensor.position.x + r + 1):
                if abs(sensor.position.y - y) + abs(sensor.position.x - x) <= r:
                    board[y - min_y, x - min_x] = RANGE
    for sensor in sensors:
        board[sensor.position.y - min_y, sensor.position.x - min_x] = SENSOR
        board[sensor.beacon.y - min_y, sensor.beacon.x - min_x] = BEACON

    print(visualize_board(board))
    target_y = 10
    adjusted_target_y = target_y - min_y
    target_row = board[adjusted_target_y]
    count = np.sum(target_row != EMPTY) - np.sum(target_row == BEACON)
    return str(count)


def visualize_board(board: npt.NDArray[np.uint8]) -> str:
    height, width = board.shape
    char_map = {EMPTY: ".", SENSOR: "S", BEACON: "B", RANGE: "*"}
    rows = ("".join(map(char_map.__getitem__, row)) for row in board)
    content = "\n".join(map(lambda s: f"|{s}|", rows))
    edge = "-" * (width + 2)
    return "\n".join([edge, content, edge])


if __name__ == "__main__":
    setup_logging()
    main()
