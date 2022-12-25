import functools
import io
import itertools as it
import logging
import operator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, NamedTuple

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
    north_exit: Point
    south_exit: Point
    blizzards: list[Blizzard]
    levels_cache: dict[int, set[Point]] = field(default_factory=dict)

    def generate_level(self, t: int) -> set[Point]:
        return {
            Point(
                y=(blizzard.initial_position.y + t * blizzard.velocity.y) % self.height,
                x=(blizzard.initial_position.x + t * blizzard.velocity.x) % self.width,
            )
            for blizzard in self.blizzards
        }

    def __getitem__(self, t: int) -> set[Point]:
        if t not in self.levels_cache:
            self.levels_cache[t] = self.generate_level(t)
        return self.levels_cache[t]

    @functools.cached_property
    def almost_south_exit(self) -> Point:
        return Point(y=self.south_exit.y - 1, x=self.south_exit.x)

    @functools.cached_property
    def almost_north_exit(self) -> Point:
        return Point(y=self.north_exit.y + 1, x=self.north_exit.x)


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
    north_exit = Point(y=-1, x=0)
    south_exit: Point
    row = 0
    for line in trimmed_lines:
        assert len(line) == width
        if line.startswith("#"):
            assert line.endswith(".")
            south_exit = Point(y=row, x=width - 1)
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
        north_exit=north_exit,
        south_exit=south_exit,
        blizzards=blizzards,
    )


class PositionInTime(NamedTuple):
    time: int
    position: Point


def get_possible_positions(current: Point, board: Board) -> Iterable[Point]:
    yield current  # wait

    if current == board.north_exit:
        yield board.almost_north_exit
        return

    if current == board.south_exit:
        yield board.almost_south_exit
        return

    if current.y > 0:
        yield Point(y=current.y - 1, x=current.x)
    if current.y < board.height - 1:
        yield Point(y=current.y + 1, x=current.x)
    if current.x > 0:
        yield Point(y=current.y, x=current.x - 1)
    if current.x < board.width - 1:
        yield Point(y=current.y, x=current.x + 1)

    if current == board.almost_north_exit:
        yield board.north_exit

    if current == board.almost_south_exit:
        yield board.south_exit


def get_unvisited_neighbours(
    board: Board, visited: set[PositionInTime], current: PositionInTime
) -> Iterable[PositionInTime]:
    next_turn = current.time + 1
    # First figure out which positions are possible (board geometry wise)
    possible_positions = get_possible_positions(current.position, board)
    # then discard the ones that are occupied by blizzards
    empty_positions = it.filterfalse(board[next_turn].__contains__, possible_positions)
    empty_positions_in_time = map(
        functools.partial(PositionInTime, next_turn), empty_positions
    )
    # then discard the ones that we have already visited
    unvisited_positions = it.filterfalse(visited.__contains__, empty_positions_in_time)
    return unvisited_positions


def find_min_distance(
    board: Board, *, start_point: PositionInTime, end_position: Point
) -> PositionInTime:
    distances: dict[PositionInTime, int] = {start_point: 0}
    visited: set[PositionInTime] = set()
    max_t = start_point.time

    while True:
        # choose an unvisited position with smallest distance (cost)
        unvisited = set(distances) - visited
        current = min(unvisited, key=distances.__getitem__)
        logger.debug("Visiting %s", current)
        if current.time > max_t:
            max_t = current.time
            logger.info("Considering t=%s", max_t)
        current_cost = distances[current]
        neighbours = get_unvisited_neighbours(board, visited, current)
        cost = current_cost + 1
        for neighbour in neighbours:
            logger.debug("  Neighbour %s", neighbour)
            distances[neighbour] = cost
            if neighbour.position == end_position:
                logger.debug("    Got just next to the exit")
                return neighbour
        visited.add(current)


def visualize(board: Board, position: PositionInTime) -> str:
    level = board[position.time]
    buf = io.StringIO()
    for y in range(board.height):
        for x in range(board.width):
            point = Point(y=y, x=x)
            if point == position.position:
                buf.write("@")
            elif point in level:
                buf.write("$")
            else:
                buf.write(".")
        buf.write("\n")
    return buf.getvalue()


@wrap_main
def main(filename: Path) -> str:
    board = read_board(filename)
    # for t in range(3):
    #     logger.debug(
    #         "Plain board t=%d\n%s",
    #         t,
    #         visualize(board, PositionInTime(t, Point(y=-1, x=-1))),
    #     )
    end_point = find_min_distance(
        board,
        start_point=PositionInTime(0, board.north_exit),
        end_position=board.south_exit,
    )
    logger.info("Crosses the exit at %s", end_point)
    return str(end_point.time)


if __name__ == "__main__":
    setup_logging(logging.INFO)
    main()
