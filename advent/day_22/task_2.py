import enum
import logging
from pathlib import Path
from typing import NamedTuple

import click
import numpy as np
from numpy import typing as npt

from ..logs import setup_logging
from .task_1 import (
    BoardVisualization,
    Direction,
    InstructionsType,
    Position,
    Rotation,
    Tile,
    find_starting_point,
    hash_position,
    read_data,
)

logger = logging.getLogger(__name__)


class Board(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"


class Transform(str, enum.Enum):
    MIRROR = "M"
    KEEP = "K"
    SWAP = "S"
    SWAP_MIRROR = "SM"


class Transition(NamedTuple):
    target: Board
    new_direction: Direction
    x: Transform
    y: Transform


SAMPLE_TRANSITIONS: dict[Board, dict[Direction, Transition]] = {
    Board.A: {
        Direction.UP: Transition(
            Board.E, Direction.DOWN, x=Transform.MIRROR, y=Transform.KEEP
        ),
        Direction.RIGHT: Transition(
            Board.D, Direction.LEFT, x=Transform.KEEP, y=Transform.MIRROR
        ),
        Direction.DOWN: Transition(
            Board.B, Direction.DOWN, x=Transform.KEEP, y=Transform.MIRROR
        ),
        Direction.LEFT: Transition(
            Board.F, Direction.DOWN, x=Transform.SWAP, y=Transform.SWAP
        ),
    },
    Board.B: {
        Direction.UP: Transition(
            Board.A, Direction.UP, x=Transform.KEEP, y=Transform.MIRROR
        ),
        Direction.RIGHT: Transition(  # Verified
            Board.D, Direction.DOWN, x=Transform.SWAP_MIRROR, y=Transform.SWAP_MIRROR
        ),
        Direction.DOWN: Transition(
            Board.C, Direction.DOWN, x=Transform.KEEP, y=Transform.MIRROR
        ),
        Direction.LEFT: Transition(
            Board.F, Direction.LEFT, x=Transform.MIRROR, y=Transform.KEEP
        ),
    },
    Board.C: {
        Direction.UP: Transition(
            Board.B, Direction.UP, x=Transform.KEEP, y=Transform.MIRROR
        ),
        Direction.RIGHT: Transition(
            Board.D, Direction.RIGHT, x=Transform.MIRROR, y=Transform.KEEP
        ),
        Direction.DOWN: Transition(
            Board.E, Direction.UP, x=Transform.MIRROR, y=Transform.KEEP
        ),
        Direction.LEFT: Transition(
            Board.F, Direction.UP, x=Transform.SWAP_MIRROR, y=Transform.SWAP_MIRROR
        ),
    },
    Board.D: {
        Direction.LEFT: Transition(
            Board.C, Direction.LEFT, x=Transform.MIRROR, y=Transform.KEEP
        ),
        Direction.DOWN: Transition(
            Board.E, Direction.RIGHT, x=Transform.SWAP_MIRROR, y=Transform.SWAP_MIRROR
        ),
    },
    Board.E: {
        Direction.DOWN: Transition(
            Board.C, Direction.UP, x=Transform.MIRROR, y=Transform.KEEP
        ),
        Direction.RIGHT: Transition(
            Board.F, Direction.RIGHT, x=Transform.MIRROR, y=Transform.KEEP
        ),
    },
    Board.F: {
        Direction.UP: Transition(
            Board.A, Direction.RIGHT, x=Transform.SWAP, y=Transform.SWAP
        ),
    },
}

INPUT_TRANSITIONS: dict[Board, dict[Direction, Transition]] = {
    Board.A: {
        Direction.UP: Transition(
            Board.E, Direction.RIGHT, x=Transform.SWAP, y=Transform.SWAP
        ),
        Direction.LEFT: Transition(
            Board.D, Direction.RIGHT, x=Transform.KEEP, y=Transform.MIRROR
        ),
        Direction.RIGHT: Transition(
            Board.F, Direction.RIGHT, x=Transform.MIRROR, y=Transform.KEEP
        ),
        Direction.DOWN: Transition(
            Board.B, Direction.DOWN, x=Transform.KEEP, y=Transform.MIRROR
        ),
    },
    Board.B: {
        Direction.RIGHT: Transition(
            Board.F, Direction.UP, x=Transform.SWAP, y=Transform.SWAP
        ),
        Direction.DOWN: Transition(
            Board.C, Direction.DOWN, x=Transform.KEEP, y=Transform.MIRROR
        ),
        Direction.LEFT: Transition(
            Board.D, Direction.DOWN, x=Transform.SWAP, y=Transform.SWAP
        ),
        Direction.UP: Transition(
            Board.A, Direction.UP, x=Transform.KEEP, y=Transform.MIRROR
        ),
    },
    Board.C: {
        Direction.UP: Transition(
            Board.B, Direction.UP, x=Transform.KEEP, y=Transform.MIRROR
        ),
        Direction.LEFT: Transition(
            Board.D, Direction.LEFT, x=Transform.MIRROR, y=Transform.KEEP
        ),
        Direction.RIGHT: Transition(
            Board.F, Direction.LEFT, x=Transform.KEEP, y=Transform.MIRROR
        ),
        Direction.DOWN: Transition(
            Board.E, Direction.LEFT, x=Transform.SWAP, y=Transform.SWAP
        ),
    },
    Board.D: {
        Direction.LEFT: Transition(
            Board.A, Direction.RIGHT, x=Transform.KEEP, y=Transform.MIRROR
        ),
        Direction.DOWN: Transition(
            Board.E, Direction.DOWN, x=Transform.KEEP, y=Transform.MIRROR
        ),
        Direction.RIGHT: Transition(
            Board.C, Direction.RIGHT, x=Transform.MIRROR, y=Transform.KEEP
        ),
        Direction.UP: Transition(
            Board.B, Direction.RIGHT, x=Transform.SWAP, y=Transform.SWAP
        ),
    },
    Board.E: {
        Direction.LEFT: Transition(
            Board.A, Direction.DOWN, x=Transform.SWAP, y=Transform.SWAP
        ),
        Direction.UP: Transition(
            Board.D, Direction.UP, x=Transform.KEEP, y=Transform.MIRROR
        ),
        Direction.DOWN: Transition(
            Board.F, Direction.DOWN, x=Transform.KEEP, y=Transform.MIRROR
        ),
        Direction.RIGHT: Transition(
            Board.C, Direction.UP, x=Transform.SWAP, y=Transform.SWAP
        ),
    },
    Board.F: {
        Direction.UP: Transition(
            Board.E, Direction.UP, x=Transform.KEEP, y=Transform.MIRROR
        ),
        Direction.DOWN: Transition(
            Board.B, Direction.LEFT, x=Transform.SWAP, y=Transform.SWAP
        ),
        Direction.RIGHT: Transition(
            Board.C, Direction.LEFT, x=Transform.KEEP, y=Transform.MIRROR
        ),
        Direction.LEFT: Transition(
            Board.A, Direction.LEFT, x=Transform.MIRROR, y=Transform.KEEP
        ),
    },
}

SAMPLE_SUPER_TILES: list[list[Board | None]] = [
    [None, None, Board.A, None],
    [Board.E, Board.F, Board.B, None],
    [None, None, Board.C, Board.D],
]

INPUT_SUPER_TILES: list[list[Board | None]] = [
    [None, Board.A, Board.F],
    [None, Board.B, None],
    [Board.D, Board.C, None],
    [Board.E, None, None],
]


class MiniBoard(NamedTuple):
    tiles: npt.NDArray[np.uint8]
    original_indices: npt.NDArray[np.int16]


def get_superboard(
    board: npt.NDArray[np.uint8], super_tiles: list[list[Board | None]]
) -> dict[Board, MiniBoard]:
    result: dict[Board, MiniBoard] = {}
    height, width = board.shape
    original_indices = np.full((height, width, 2), -1, dtype=np.int16)
    for y in range(height):
        for x in range(width):
            original_indices[y, x] = (y, x)
    super_tiles_array = np.array(super_tiles, dtype=object)
    sup_height, sup_width = super_tiles_array.shape
    block_size = width // sup_width
    logger.debug("Block size %d", block_size)
    for super_y in range(sup_height):
        for super_x in range(sup_width):
            super_tile = super_tiles_array[super_y, super_x]
            if super_tile is None:
                continue
            assert isinstance(super_tile, Board)
            tile = board[
                super_y * block_size : (super_y + 1) * block_size,
                super_x * block_size : (super_x + 1) * block_size,
            ]
            indices = original_indices[
                super_y * block_size : (super_y + 1) * block_size,
                super_x * block_size : (super_x + 1) * block_size,
            ]
            result[super_tile] = MiniBoard(tile, indices)
    return result


def recover_point(
    superboard: dict[Board, MiniBoard], board: Board, point: Position
) -> Position:
    miniboard = superboard[board]
    original_y, original_x = miniboard.original_indices[point]
    return Position(y=original_y, x=original_x)


def execute_instructions(
    transitions: dict[Board, dict[Direction, Transition]],
    superboard: dict[Board, MiniBoard],
    board: Board,
    point: Position,
    direction: Direction,
    instructions: InstructionsType,
) -> tuple[Board, Position, Direction]:
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
                BoardVisualization(superboard[board].tiles, point, direction),
            )
        else:
            assert isinstance(instruction, int)
            logger.debug("Moving %d steps in direction %s", instruction, direction.name)
            for step in range(1, instruction + 1):
                logger.debug(
                    "Making step %d from %r\n%s",
                    step,
                    point,
                    BoardVisualization(superboard[board].tiles, point, direction),
                )
                new_board, new_point, new_direction = get_next_point(
                    transitions, superboard, board, point, direction
                )
                new_value = superboard[new_board].tiles[new_point]
                if new_value == Tile.EMPTY:
                    logger.debug("Can move into an empty space")
                    point = new_point
                    board = new_board
                    direction = new_direction
                else:
                    assert new_value == Tile.WALL
                    logger.debug("Hit a wall")
                    break
            logger.debug(
                "Movement finished at %s %r %s\n%s",
                board,
                point,
                direction,
                BoardVisualization(superboard[board].tiles, point, direction),
            )
    return board, point, direction


def get_transition(
    transitions: dict[Board, dict[Direction, Transition]],
    board: Board,
    exit_direction: Direction,
) -> Transition:
    board_transitions = transitions[board]
    try:
        return board_transitions[exit_direction]
    except KeyError:
        raise KeyError(board, exit_direction)


def get_next_point(
    transitions: dict[Board, dict[Direction, Transition]],
    superboard: dict[Board, MiniBoard],
    board: Board,
    point: Position,
    direction: Direction,
) -> tuple[Board, Position, Direction]:
    miniboard = superboard[board]
    height, width = miniboard.tiles.shape
    assert height == width
    size = height
    y, x = point
    if direction == Direction.UP:
        if y == 0:
            transition = get_transition(transitions, board, direction)
            return apply_transition(transition, point, size=size)
        else:
            y -= 1
    elif direction == Direction.RIGHT:
        if x == width - 1:
            transition = get_transition(transitions, board, direction)
            return apply_transition(transition, point, size=size)
        else:
            x += 1
    elif direction == Direction.DOWN:
        if y == height - 1:
            transition = get_transition(transitions, board, direction)
            return apply_transition(transition, point, size=size)
        else:
            y += 1
    else:
        assert direction == Direction.LEFT
        if x == 0:
            transition = get_transition(transitions, board, direction)
            return apply_transition(transition, point, size=size)
        else:
            x -= 1
    return board, Position(y=y, x=x), direction


def transform(coord: int, transform: Transform, *, other: int, size: int) -> int:
    if transform == Transform.KEEP:
        return coord
    elif transform == Transform.MIRROR:
        # from 0 to size - 1
        # from size - 1 to 0
        return size - coord - 1
    elif transform == Transform.SWAP:
        return other
    else:
        assert transform == Transform.SWAP_MIRROR
        return size - other - 1


def apply_transition(
    transition: Transition,
    point: Position,
    *,
    size: int,
) -> tuple[Board, Position, Direction]:
    new_board = transition.target
    new_direction = transition.new_direction

    x = transform(point.x, transition.x, other=point.y, size=size)
    y = transform(point.y, transition.y, other=point.x, size=size)

    return new_board, Position(y=y, x=x), new_direction


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
@click.option("--is-input/--is-sample", help="Is input or sample", required=True)
def main(filename: Path, is_input: bool) -> None:
    logger.debug("Reading data")
    board, instructions = read_data(filename)
    superboard = get_superboard(
        board, INPUT_SUPER_TILES if is_input else SAMPLE_SUPER_TILES
    )
    del board
    logger.debug("Looking for starting point")
    start_board = Board.A
    start_point = find_starting_point(superboard[start_board].tiles)
    logger.debug("Starting point found %r", start_point)
    start_direction = Direction.RIGHT

    end_board, end_point, end_direction = execute_instructions(
        INPUT_TRANSITIONS if is_input else SAMPLE_TRANSITIONS,
        superboard,
        start_board,
        start_point,
        start_direction,
        instructions,
    )
    logger.debug(
        "End board=%s, point=%r, direction=%s", end_board, end_point, end_direction
    )
    recovered_point = recover_point(superboard, end_board, end_point)
    logger.debug("Recovered point %r", recovered_point)
    click.echo(str(hash_position(recovered_point, end_direction)))


if __name__ == "__main__":
    setup_logging(logging.INFO)
    main()
