import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, NamedTuple

import numpy as np
import numpy.typing as npt

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines
from ..logs import setup_logging

logger = logging.getLogger(__name__)


class Position(NamedTuple):
    y: int
    x: int


@dataclass
class Board:
    tiles: npt.NDArray[np.uint8]
    start_position: Position
    end_position: Position


def parse_board(filename: Path) -> Board:
    start_position: Position | None = None
    end_position: Position | None = None
    lines: list[list[int]] = []
    a_ord = ord("a")
    for row_idx, line in enumerate(get_stripped_lines(filename)):
        if "S" in line:
            assert start_position is None
            start_position = Position(x=line.index("S"), y=row_idx)
            line = line.replace("S", "a")
        if "E" in line:
            assert end_position is None
            end_position = Position(x=line.index("E"), y=row_idx)
            line = line.replace("E", "z")
        elevations = [ord(c) - a_ord for c in line]
        lines.append(elevations)
    tiles = np.array(lines, dtype=np.uint8)
    assert start_position is not None
    assert end_position is not None
    return Board(tiles=tiles, start_position=start_position, end_position=end_position)


def argmin2d(array: npt.NDArray[np.uint32]) -> Position:
    y, x = np.unravel_index(np.argmin(array), array.shape)
    return Position(y=y, x=x)


def find_path(board: Board) -> int:
    logger.debug(
        "Searching for best path between %s and %s",
        board.start_position,
        board.end_position,
    )
    height, width = board.tiles.shape
    visited = np.zeros_like(board.tiles, dtype=np.bool)
    costs = np.full_like(
        board.tiles, fill_value=np.iinfo(np.uint32).max, dtype=np.uint32
    )
    costs[board.start_position] = 0

    def get_unvisited_neighbors(position: Position) -> Iterable[Position]:
        current_elevation = board.tiles[position]
        north = Position(y=position.y - 1, x=position.x)
        if (
            north.y >= 0
            and not visited[north]
            and board.tiles[north] <= current_elevation + 1
        ):
            yield north
        south = Position(y=position.y + 1, x=position.x)
        if (
            south.y < height
            and not visited[south]
            and board.tiles[south] <= current_elevation + 1
        ):
            yield south
        west = Position(y=position.y, x=position.x - 1)
        if (
            west.x >= 0
            and not visited[west]
            and board.tiles[west] <= current_elevation + 1
        ):
            yield west
        east = Position(y=position.y, x=position.x + 1)
        if (
            east.x < width
            and not visited[east]
            and board.tiles[east] <= current_elevation + 1
        ):
            yield east

    while not np.all(visited):
        # get 2d index of lowest cost item
        lowest_cost_index = argmin2d(np.where(visited, np.inf, costs))
        lowest_cost = costs[lowest_cost_index]
        logger.debug("Visiting %s with cost %d", lowest_cost_index, lowest_cost)
        unvisited_neighbors = get_unvisited_neighbors(lowest_cost_index)
        for neighbor_idx in unvisited_neighbors:
            costs[neighbor_idx] = lowest_cost + 1
            logger.debug(
                "Found neighbor %s with cost %d", neighbor_idx, lowest_cost + 1
            )
            if neighbor_idx == board.end_position:
                break
        visited[lowest_cost_index] = True

    best_cost: int = costs[board.end_position]
    return best_cost


@wrap_main
def main(filename: Path) -> str:
    board = parse_board(filename)
    cost = find_path(board)
    return str(cost)


if __name__ == "__main__":
    setup_logging()
    main()
