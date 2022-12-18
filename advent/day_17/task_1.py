import enum
import functools
import io
import logging
import operator
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

import tqdm

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines
from ..logs import setup_logging


class Direction(str, enum.Enum):
    LEFT = "<"
    RIGHT = ">"


logger = logging.getLogger(__name__)

ROCKS: list[tuple[int, ...]] = [
    (int("000111100", 2),),
    (int("000010000", 2), int("000111000", 2), int("000010000", 2)),
    (int("000001000", 2), int("000001000", 2), int("000111000", 2)),
    (
        int("000100000", 2),
        int("000100000", 2),
        int("000100000", 2),
        int("000100000", 2),
    ),
    (int("000110000", 2), int("000110000", 2)),
]

WIDTH = 7
FLOOR = int("111111111", 2)
TUNNEL = int("100000001", 2)

MASK = int("011111110", 2)


def _visualize_board(board: Sequence[int]) -> str:
    buf = io.StringIO()
    for row in board[::-1]:
        bits = bin(row)[2:].rjust(7, "0").replace("0", ".").replace("1", "#")
        buf.write(bits)
        buf.write("\n")
    return buf.getvalue()


@functools.cache
def move_rock(rock: tuple[int, ...], direction: Direction) -> tuple[int, ...]:
    if direction == Direction.LEFT:
        return tuple(row << 1 for row in rock)
    else:
        assert direction == Direction.RIGHT
        return tuple(row >> 1 for row in rock)


SignatureType = tuple[tuple[int, ...], int, int]


@dataclass
class Simulator:
    directions: list[Direction]
    board: list[int] = field(default_factory=lambda: [FLOOR], init=False)
    rock_idx: int = field(default=0, init=False)
    jet_idx: int = field(default=0, init=False)

    def get_board_signature(self) -> tuple[int, ...]:
        visited: dict[int, set[int]] = defaultdict(set)
        to_visit: deque[tuple[int, int]] = deque()
        to_visit.append((int("000010000", 2), len(self.board) - 1))
        while to_visit:
            mask, row = to_visit.popleft()
            mask_left = mask << 1
            if (
                not (mask_left & self.board[row]) and mask_left not in visited[row]
            ):  # free spot on the right
                to_visit.append((mask_left, row))
            mask_right = mask >> 1
            if (
                not (mask_right & self.board[row]) and mask_right not in visited[row]
            ):  # free spot on the left
                to_visit.append((mask_right, row))
            if (
                not (mask & self.board[row - 1]) and mask not in visited[row - 1]
            ):  # free spot below
                to_visit.append((mask, row - 1))
            visited[row].add(mask)
        return tuple(
            functools.reduce(operator.or_, items)
            for items in reversed(visited.values())
        )

    def get_signature(self) -> SignatureType:
        return self.get_board_signature(), self.rock_idx, self.jet_idx

    def visualize_board(self) -> None:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Board:\n%s", _visualize_board(self.board))

    def find_top_index(self) -> int:
        idx = len(self.board) - 1
        for row in self.board[::-1]:
            if row & MASK:
                return idx
            idx -= 1
        raise AssertionError()

    def clashes(
        self,
        rock: tuple[int, ...],
        top: int,
    ) -> bool:
        for idx, row in enumerate(rock):
            if self.board[top - idx] & row:
                return True
        return False

    def materialize_rock(self, rock: tuple[int, ...], top: int) -> None:
        for idx, row in enumerate(rock):
            self.board[top - idx] |= row

    def simulate_step(self) -> None:
        logger.debug("Simulating step of rock %s", self.rock_idx)
        rock = ROCKS[self.rock_idx]
        rock_height = len(rock)
        # spawn new rock
        current_top_idx = self.find_top_index()
        logger.debug("Current top index: %s", current_top_idx)
        bottom_spawn_idx = current_top_idx + 3
        logger.debug("Bottom spawn index: %s", bottom_spawn_idx)
        top_spawn_idx = bottom_spawn_idx + rock_height
        logger.debug("Needed spawn top index: %s", top_spawn_idx)
        # intitial spawn positions
        top = top_spawn_idx
        # expand board if neecessary
        while len(self.board) <= top_spawn_idx:
            logger.debug("Adding new row to board")
            self.board.append(TUNNEL)
        # visualize_board(board)

        while True:
            direction = self.directions[self.jet_idx]
            self.jet_idx = (self.jet_idx + 1) % len(self.directions)
            moved_rock = move_rock(rock, direction)
            if self.clashes(moved_rock, top):
                logger.debug("Jet stream cannot move rock")
            else:
                logger.debug("Jet stream moves rock %s", direction.name)
                rock = moved_rock

            if self.clashes(rock, top - 1):
                logger.debug("Rock cannot fall anymore")
                break
            else:
                logger.debug("Rock falls")
                top -= 1

        self.materialize_rock(rock, top)
        self.rock_idx = (self.rock_idx + 1) % len(ROCKS)

    def simulate(self, steps: int) -> int:
        cache: dict[SignatureType, tuple[int, int]] = {}
        step = 0
        extra_height = 0
        board_at_step: dict[int, str] = {}
        with tqdm.tqdm(total=steps) as pbar:
            while step < steps:
                self.simulate_step()
                self.visualize_board()
                step += 1
                pbar.update(1)

                signature = self.get_signature()
                current_height = self.find_top_index()
                if signature in cache:
                    prev_step, prev_height = cache[signature]
                    cycle_length = step - prev_step
                    height_diff = current_height - prev_height
                    logger.info(
                        "Found cycle %d -> %d (length %d), height %d -> %d (diff %d)",
                        prev_step,
                        step,
                        cycle_length,
                        prev_height,
                        current_height,
                        height_diff,
                    )
                    # current_board_state = _visualize_board(simulator.board)
                    # prev_board_state = board_at_step[prev_step]
                    # breakpoint()
                    repetitions = (steps - step) // cycle_length
                    step += cycle_length * repetitions
                    extra_height += height_diff * repetitions
                    logger.info(
                        "Skipping %d steps, adding %d height times %d",
                        cycle_length,
                        height_diff,
                        repetitions,
                    )

                    logger.info("Continuing simulation")
                    cache.clear()
                    continue

                    # break
                board_at_step[step] = _visualize_board(self.board)
                cache[signature] = step, current_height

        return self.find_top_index() + extra_height


@wrap_main
def main(filename: Path) -> str:
    directions = get_directions(filename)
    simulator = Simulator(directions)
    steps = 2022
    height = simulator.simulate(steps)
    logger.info(
        "Board after %s steps:\n%s", steps, _visualize_board(simulator.board[-50:])
    )
    return str(height)


def get_directions(filename: Path) -> list[Direction]:
    (jet_pattern,) = get_stripped_lines(filename)
    directions = list(map(Direction, jet_pattern))
    return directions


if __name__ == "__main__":
    setup_logging(logging.INFO)
    main()
