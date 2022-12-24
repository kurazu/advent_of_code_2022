import enum
import functools
import itertools as it
import logging
import operator
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, NamedTuple

import numpy as np
import tqdm
from numpy import typing as npt

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines
from ..logs import setup_logging

logger = logging.getLogger(__name__)


class Point(NamedTuple):
    y: int
    x: int


CHAR_TO_VELOCITY: dict[str, Point] = {
    ">": Point(y=0, x=1),
    "<": Point(y=0, x=-1),
    "^": Point(y=-1, x=0),
    "v": Point(y=1, x=0),
}


@dataclass
class Blizzard:
    initial_position: Point
    velocity: Point


@dataclass
class Board:
    height: int
    width: int
    start_point: Point
    end_point: Point
    blizzards: list[Blizzard]

    @functools.cached_property
    def cycle_length(self) -> int:
        return self.height * self.width

    def get_level(self, t: int) -> set[Point]:
        return {
            Point(
                y=(blizzard.initial_position.y + t * blizzard.velocity.y) % self.height,
                x=(blizzard.initial_position.x + t * blizzard.velocity.x) % self.width,
            )
            for blizzard in self.blizzards
        }

    @functools.cached_property
    def levels(self) -> list[set[Point]]:
        return [self.get_level(t) for t in range(1, self.cycle_length + 1)]


def read_board(filename: Path) -> Board:
    blizzards: list[Blizzard] = []
    trimmed_lines = iter(
        map(
            operator.itemgetter(slice(1, -1)),
            get_stripped_lines(filename),
        )
    )
    first_line = next(trimmed_lines)
    assert first_line.startswith(".#")
    width = len(first_line)
    start_point = Point(y=0, x=0)
    end_point: Point
    row = 0
    for line in trimmed_lines:
        assert len(line) == width
        if line.startswith("#"):
            assert line.endswith(".")
            end_point = Point(y=row - 1, x=width - 1)
            break
        for col, char in enumerate(line):
            if char == ".":
                continue
            initial_position = Point(y=row, x=col)
            velocity = CHAR_TO_VELOCITY[char]
            blizzards.append(
                Blizzard(
                    initial_position=initial_position,
                    velocity=velocity,
                )
            )
        row += 1
    return Board(
        height=row,
        width=width,
        start_point=start_point,
        end_point=end_point,
        blizzards=blizzards,
    )


class PositionInTime(NamedTuple):
    time: int
    position: Point


def get_possible_positions(
    current: Point, *, width: int, height: int
) -> Iterable[Point]:
    yield current  # wait
    if current.y > 0:
        yield Point(y=current.y - 1, x=current.x)
    if current.y < height - 1:
        yield Point(y=current.y + 1, x=current.x)
    if current.x > 0:
        yield Point(y=current.y, x=current.x - 1)
    if current.x < width - 1:
        yield Point(y=current.y, x=current.x + 1)


def get_unvisited_neighbours(
    board: Board, visited: set[PositionInTime], current: PositionInTime
) -> Iterable[PositionInTime]:
    next_turn = (current.time + 1) % board.cycle_length
    # First figure out which positions are possible (board geometry wise)
    possible_positions = get_possible_positions(
        current.position, width=board.width, height=board.height
    )
    # then discard the ones that are occupied by blizzards
    empty_positions = it.filterfalse(
        board.levels[next_turn].__contains__, possible_positions
    )
    empty_positions_in_time = map(
        functools.partial(PositionInTime, next_turn), empty_positions
    )
    # then discard the ones that we have already visited
    unvisited_positions = it.filterfalse(visited.__contains__, empty_positions_in_time)
    return unvisited_positions


def find_min_distance(board: Board) -> int:
    distances: dict[PositionInTime, int] = {
        PositionInTime(time=-1, position=board.start_point): 0,
    }
    visited: set[PositionInTime] = set()
    with tqdm.tqdm(
        total=board.height * board.width * board.cycle_length
    ) as progress_bar:
        while True:
            # choose an unvisited position with smallest distance (cost)
            unvisited = set(distances) - visited
            current = min(unvisited, key=distances.__getitem__)
            logger.debug("Visiting %s", current)
            cost = distances[current]
            neighbours = get_unvisited_neighbours(board, visited, current)
            for neighbour in neighbours:
                distances[neighbour] = cost + 1
                if neighbour.position == board.end_point:
                    return distances[neighbour] + 1
            visited.add(current)
            progress_bar.update()


@wrap_main
def main(filename: Path) -> str:
    board = read_board(filename)
    min_distance = find_min_distance(board)
    return str(min_distance)


if __name__ == "__main__":
    setup_logging()
    main()
