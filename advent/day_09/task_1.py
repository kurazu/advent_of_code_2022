import logging
import math
from enum import Enum
from pathlib import Path
from typing import Iterable, NamedTuple

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines

logger = logging.getLogger(__name__)


class Direction(str, Enum):
    UP = "U"
    DOWN = "D"
    LEFT = "L"
    RIGHT = "R"


class Instruction(NamedTuple):
    direction: Direction
    distance: int

    def __str__(self) -> str:
        return f"{self.direction} {self.distance}"


class Position(NamedTuple):
    x: int
    y: int

    def __str__(self) -> str:
        return f"({self.x}, {self.y})"


def parse_instructions(filename: Path) -> Iterable[Instruction]:
    for line in get_stripped_lines(filename):
        direction_str, distance_str = line.split(" ")
        yield Instruction(Direction(direction_str), int(distance_str))


def tail_catchup(tail_location: Position, head_location: Position) -> Position:
    x_diff = head_location.x - tail_location.x
    x_step = int(math.copysign(1, x_diff))
    y_diff = head_location.y - tail_location.y
    y_step = int(math.copysign(1, y_diff))
    logger.debug(
        "head @ %s, tail @ %s, Δx=%s, Δy=%s",
        head_location,
        tail_location,
        x_diff,
        y_diff,
    )

    new_tail_location: Position
    if abs(x_diff) <= 1 and abs(y_diff) <= 1:
        logger.debug("Tail is cought up, NOOP")
        new_tail_location = tail_location
    elif abs(x_diff) == 2 and abs(y_diff) == 0:
        logger.debug("Tail jumping X")
        new_tail_location = Position(tail_location.x + x_step, tail_location.y)
    elif abs(y_diff) == 2 and abs(x_diff) == 0:
        logger.debug("Tail jumping Y")
        new_tail_location = Position(tail_location.x, tail_location.y + y_step)
    else:
        logger.debug("Tail moving diagonally")
        new_tail_location = Position(tail_location.x + x_step, tail_location.y + y_step)
    logger.debug("New tail location: %s", new_tail_location)
    return new_tail_location


def execute_instructions(instructions: Iterable[Instruction]) -> set[Position]:
    tail_visited_locations: set[Position] = set()
    head_location = Position(0, 0)
    tail_location = Position(0, 0)
    visualize_visited_locations(
        tail_visited_locations, head=head_location, tail=tail_location
    )
    for instruction in instructions:
        logger.debug("Processing instruction %s", instruction)
        for _ in range(instruction.distance):
            if instruction.direction == Direction.UP:
                head_location = Position(head_location.x, head_location.y - 1)
            elif instruction.direction == Direction.DOWN:
                head_location = Position(head_location.x, head_location.y + 1)
            elif instruction.direction == Direction.LEFT:
                head_location = Position(head_location.x - 1, head_location.y)
            else:
                assert instruction.direction == Direction.RIGHT
                head_location = Position(head_location.x + 1, head_location.y)
            tail_location = tail_catchup(tail_location, head_location)
            tail_visited_locations.add(tail_location)
            visualize_visited_locations(
                tail_visited_locations, head=head_location, tail=tail_location
            )
    return tail_visited_locations


def visualize_visited_locations(
    visited_locations: set[Position],
    *,
    head: Position | None = None,
    tail: Position | None = None,
) -> None:
    import numpy as np

    all_locations = visited_locations
    if head is not None:
        all_locations.add(head)
    if tail is not None:
        all_locations.add(tail)

    min_x = min(location.x for location in all_locations)
    max_x = max(location.x for location in all_locations)
    min_y = min(location.y for location in all_locations)
    max_y = max(location.y for location in all_locations)
    x_diff = max_x - min_x
    y_diff = max_y - min_y
    board = np.zeros((y_diff + 1, x_diff + 1), dtype=str)
    board[:] = " "
    for location in visited_locations:
        board[location.y - min_y, location.x - min_x] = "#"
    if head is not None:
        board[head.y - min_y, head.x - min_x] = "H"
    if tail is not None:
        board[tail.y - min_y, tail.x - min_x] = "T"
    if head is not None and tail is not None and head == tail:
        board[head.y - min_y, head.x - min_x] = "X"
    logger.debug("\n".join("".join(row) for row in board))


@wrap_main
def main(filename: Path) -> str:
    instructions = parse_instructions(filename)
    visited_locations = execute_instructions(instructions)
    visualize_visited_locations(visited_locations)
    return str(len(visited_locations))


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(message)s")
    main()
