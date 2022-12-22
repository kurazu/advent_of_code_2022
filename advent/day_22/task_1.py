import enum
import io
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

import numpy as np
from numpy import typing as npt

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines
from ..logs import setup_logging

logger = logging.getLogger(__name__)


class Tile(int, enum.Enum):
    VOID = 0
    EMPTY = 1
    WALL = 2


class Rotation(str, enum.Enum):
    CLOCKWISE = "R"
    COUNTER_CLOCKWISE = "L"


class Direction(int, enum.Enum):
    RIGHT = 0
    DOWN = 1
    LEFT = 2
    UP = 3


BoardType = npt.NDArray[np.uint8]
InstructionsType = list[int | Rotation]

CHAR_TO_TILE = {
    " ": Tile.VOID,
    ".": Tile.EMPTY,
    "#": Tile.WALL,
}
TILE_TO_CHAR = {v: k for k, v in CHAR_TO_TILE.items()}


def parse_instructions(line: str) -> InstructionsType:
    instructions: InstructionsType = []
    digits: list[str] = []
    for c in line:
        if c in {"L", "R"}:
            if digits:
                instructions.append(int("".join(digits)))
                digits.clear()
            instructions.append(Rotation(c))
        else:
            digits.append(c)
    if digits:
        instructions.append(int("".join(digits)))
    return instructions


class Position(NamedTuple):
    y: int
    x: int


def read_data(filename: Path) -> tuple[BoardType, InstructionsType]:
    lines = iter(get_stripped_lines(filename))
    board: list[list[Tile]] = []
    for line in lines:
        if line == "":
            break
        row = [CHAR_TO_TILE[c] for c in line]
        board.append(row)
    instructions = parse_instructions(next(lines))
    max_row_lenght = max(map(len, board))
    for row in board:
        while len(row) < max_row_lenght:
            row.append(Tile.VOID)
    board_array = np.array(board, dtype=np.uint8)
    return board_array, instructions


def find_starting_point(board: BoardType) -> Position:
    top_row = board[0]
    (indices,) = np.where(top_row == Tile.EMPTY)
    min_x: int = np.min(indices).item()
    return Position(y=0, x=min_x)


def execute_instructions(
    board: BoardType,
    start_point: Position,
    direction: Direction,
    instructions: InstructionsType,
) -> tuple[Position, Direction]:
    current_point = start_point
    for instruction in instructions:
        if isinstance(instruction, Rotation):
            prev_direction = direction
            if instruction == Rotation.CLOCKWISE:
                direction = Direction((direction + 1) % 4)
            else:
                direction = Direction((direction - 1) % 4)
            logger.debug(
                "Rotated %s from %s to %s\n%s",
                instruction.name,
                prev_direction.name,
                direction.name,
                BoardVisualization(board, current_point, direction),
            )
        else:
            assert isinstance(instruction, int)
            logger.debug("Moving %d steps in direction %s", instruction, direction.name)
            for step in range(1, instruction + 1):
                logger.debug(
                    "Making step %d from %r\n%s",
                    step,
                    current_point,
                    BoardVisualization(board, current_point, direction),
                )
                if direction == Direction.UP:
                    current_point = move(board, current_point, dx=0, dy=-1)
                elif direction == Direction.RIGHT:
                    current_point = move(board, current_point, dx=1, dy=0)
                elif direction == Direction.DOWN:
                    current_point = move(board, current_point, dx=0, dy=1)
                else:
                    assert direction == Direction.LEFT
                    current_point = move(board, current_point, dx=-1, dy=0)
            logger.debug(
                "Movement finished at %r\n%s",
                current_point,
                BoardVisualization(board, current_point, direction),
            )
    return current_point, direction


def move(board: BoardType, current_point: Position, *, dx: int, dy: int) -> Position:
    height, width = board.shape
    n = 1
    while True:
        new_y = (current_point.y + dy * n) % height
        assert 0 <= new_y < height
        new_x = (current_point.x + dx * n) % width
        assert 0 <= new_x < width
        new_point = Position(y=new_y, x=new_x)
        board_at_new_point = board[new_point]
        if board_at_new_point == Tile.EMPTY:
            # the move is allowed to happen
            return new_point
        elif board_at_new_point == Tile.VOID:
            # the move needs to wrap around the map
            n += 1
            continue
        else:
            assert board_at_new_point == Tile.WALL
            # the move is stopped by a wall
            return current_point


@dataclass
class BoardVisualization:
    board: BoardType
    position: Position
    direction: Direction

    def __str__(self) -> str:
        height, width = self.board.shape
        buf = io.StringIO()
        character = {
            Direction.DOWN: "v",
            Direction.UP: "^",
            Direction.LEFT: "<",
            Direction.RIGHT: ">",
        }[self.direction]
        for row_idx in range(height):
            for col_idx in range(width):
                if row_idx == self.position.y and col_idx == self.position.x:
                    buf.write(character)
                else:
                    buf.write(TILE_TO_CHAR[Tile(self.board[row_idx, col_idx])])
            buf.write("\n")
        return buf.getvalue()


def hash_position(position: Position, direction: Direction) -> int:
    return (position.y + 1) * 1000 + (position.x + 1) * 4 + direction.value


@wrap_main
def main(filename: Path) -> str:
    logger.debug("Reading data")
    board, instructions = read_data(filename)
    logger.debug("Looking for starting point")
    start_point = find_starting_point(board)
    logger.debug("Starting point found %r", start_point)
    direction = Direction.RIGHT
    end_point, end_direction = execute_instructions(
        board, start_point, direction, instructions
    )
    logger.debug("End point found %r %s", end_point, end_direction.name)
    return str(hash_position(end_point, end_direction))


if __name__ == "__main__":
    setup_logging(logging.INFO)
    main()
