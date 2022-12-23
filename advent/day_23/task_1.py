import io
import itertools as it
import logging
import operator
from collections import defaultdict
from pathlib import Path
from typing import Iterable, NamedTuple, Protocol

import more_itertools as mit

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines
from ..logs import setup_logging

logger = logging.getLogger(__name__)


class Point(NamedTuple):
    y: int
    x: int


def read_board(filename: Path) -> Iterable[Point]:
    for row_idx, line in enumerate(get_stripped_lines(filename)):
        for col_idx, c in enumerate(line):
            if c == "#":
                yield Point(y=row_idx, x=col_idx)


class Check(Protocol):
    def __call__(self, elf: Point, elves: set[Point]) -> Point | None:
        ...


def top_check(elf: Point, elves: set[Point]) -> Point | None:
    n = Point(elf.y - 1, elf.x)
    nw = Point(elf.y - 1, elf.x - 1)
    ne = Point(elf.y - 1, elf.x + 1)
    if (n not in elves) and (nw not in elves) and (ne not in elves):
        return n
    else:
        return None


def left_check(elf: Point, elves: set[Point]) -> Point | None:
    w = Point(elf.y, elf.x - 1)
    nw = Point(elf.y - 1, elf.x - 1)
    sw = Point(elf.y + 1, elf.x - 1)
    if (w not in elves) and (nw not in elves) and (sw not in elves):
        return w
    else:
        return None


def right_check(elf: Point, elves: set[Point]) -> Point | None:
    e = Point(elf.y, elf.x + 1)
    ne = Point(elf.y - 1, elf.x + 1)
    se = Point(elf.y + 1, elf.x + 1)
    if (e not in elves) and (ne not in elves) and (se not in elves):
        return e
    else:
        return None


def bottom_check(elf: Point, elves: set[Point]) -> Point | None:
    s = Point(elf.y + 1, elf.x)
    sw = Point(elf.y + 1, elf.x - 1)
    se = Point(elf.y + 1, elf.x + 1)
    if (s not in elves) and (sw not in elves) and (se not in elves):
        return s
    else:
        return None


def plan_position(elf: Point, elves: set[Point], checks: list[Check]) -> Point:
    positions = [check(elf, elves) for check in checks]
    if all(positions) or not any(positions):
        logger.debug("Elf decides to stay put")
        return elf
    else:
        first = mit.first_true(positions)
        assert first is not None
        return first


def simulate(elves: set[Point], checks: list[Check]) -> set[Point]:
    plan: dict[Point, set[Point]] = defaultdict(set)
    for elf in elves:
        new_position = plan_position(elf, elves, checks)
        plan[new_position].add(elf)
    execution: set[Point] = set()
    for new_position, elves_that_want_to_move_there in plan.items():
        if len(elves_that_want_to_move_there) == 1:
            # this was the only elf that wanted to move there.
            execution.add(new_position)
        else:
            # there were multiple elves that wanted to move there.
            # they all go back to their original positions.
            execution |= elves_that_want_to_move_there
    return execution


def visualize(elves: set[Point]) -> str:
    min_y, max_y = mit.minmax(map(operator.attrgetter("y"), elves))
    min_x, max_x = mit.minmax(map(operator.attrgetter("x"), elves))
    buf = io.StringIO()
    buf.write("  ")
    for x in range(min_x, max_x + 1):
        buf.write(f"{x%10}")
    buf.write("\n")
    for y in range(min_y, max_y + 1):
        buf.write(f"{y%10} ")
        for x in range(min_x, max_x + 1):
            if Point(y=y, x=x) in elves:
                char = "#"
            else:
                char = "."
            buf.write(char)
        buf.write("\n")
    return buf.getvalue()


@wrap_main
def main(filename: Path) -> str:
    elves = set(read_board(filename))
    check_orders: list[Check] = [top_check, bottom_check, left_check, right_check] * 2
    all_checks: list[list[Check]] = [
        check_orders[offset : offset + 4] for offset in range(4)
    ]
    checks = it.cycle(all_checks)
    logger.debug("Before\n%s", visualize(elves))
    for round in range(10):
        round_checks = next(checks)
        logger.debug(
            "Round %d checks %s",
            round + 1,
            " ".join(map(operator.attrgetter("__name__"), round_checks)),
        )
        elves = simulate(elves, round_checks)
        logger.debug("After round %d\n%s", round + 1, visualize(elves))
    min_y, max_y = mit.minmax(map(operator.attrgetter("y"), elves))
    min_x, max_x = mit.minmax(map(operator.attrgetter("x"), elves))
    area = (max_x - min_x + 1) * (max_y - min_y + 1)
    count = area - len(elves)
    return str(count)


if __name__ == "__main__":
    setup_logging()
    main()
