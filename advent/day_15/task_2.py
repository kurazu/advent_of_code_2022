import logging
import re
from pathlib import Path
from typing import Iterable, NamedTuple

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


@wrap_main
def main(filename: Path) -> str:
    sensors = list(parse_sensors(filename))
    breakpoint()
    return ""


if __name__ == "__main__":
    setup_logging()
    main()
