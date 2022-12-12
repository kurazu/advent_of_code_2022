import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, NamedTuple, Protocol

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


class CanClimbCallback(Protocol):
    def __call__(self, current_elevation: int, neighbor_elevation: int) -> bool:
        ...


class EarlyStoppingCallback(Protocol):
    def __call__(self, neighbor_position: Position, neighbor_elevation: int) -> bool:
        ...


def find_path(
    tiles: npt.NDArray[np.uint8],
    *,
    start_position: Position,
    can_climb_callback: CanClimbCallback,
    early_stopping_callback: EarlyStoppingCallback,
) -> int:
    logger.debug("Searching for best path from %s", start_position)
    height, width = tiles.shape
    visited = np.zeros_like(tiles, dtype=bool)
    costs = np.full_like(tiles, fill_value=np.iinfo(np.uint32).max, dtype=np.uint32)
    costs[start_position] = 0

    def get_unvisited_neighbors(position: Position) -> Iterable[Position]:
        current_elevation = tiles[position]
        north = Position(y=position.y - 1, x=position.x)
        if (
            north.y >= 0
            and not visited[north]
            and can_climb_callback(current_elevation, tiles[north])
        ):
            yield north
        south = Position(y=position.y + 1, x=position.x)
        if (
            south.y < height
            and not visited[south]
            and can_climb_callback(current_elevation, tiles[south])
        ):
            yield south
        west = Position(y=position.y, x=position.x - 1)
        if (
            west.x >= 0
            and not visited[west]
            and can_climb_callback(current_elevation, tiles[west])
        ):
            yield west
        east = Position(y=position.y, x=position.x + 1)
        if (
            east.x < width
            and not visited[east]
            and can_climb_callback(current_elevation, tiles[east])
        ):
            yield east

    while not np.all(visited):
        # get 2d index of lowest cost item
        lowest_cost_index = argmin2d(np.where(visited, np.inf, costs))
        lowest_cost = costs[lowest_cost_index]
        logger.debug("Visiting %s with cost %d", lowest_cost_index, lowest_cost)
        unvisited_neighbors = get_unvisited_neighbors(lowest_cost_index)
        neighbor_cost: int = lowest_cost + 1
        for neighbor_idx in unvisited_neighbors:
            costs[neighbor_idx] = neighbor_cost
            logger.debug("Found neighbor %s with cost %d", neighbor_idx, neighbor_cost)
            if early_stopping_callback(neighbor_idx, tiles[neighbor_idx]):
                logger.debug("Early stopping at %s", neighbor_idx)
                return neighbor_cost
        visited[lowest_cost_index] = True

    raise AssertionError("Algorithm should have stopped early")


@wrap_main
def main(filename: Path) -> str:
    board = parse_board(filename)
    cost = find_path(
        board.tiles,
        start_position=board.start_position,
        can_climb_callback=(
            lambda current_elevation, neighbor_elevation: neighbor_elevation
            <= current_elevation + 1
        ),
        early_stopping_callback=(
            lambda neighbor_position, neighbor_elevation: neighbor_position
            == board.end_position
        ),
    )
    return str(cost)


if __name__ == "__main__":
    setup_logging()
    main()
