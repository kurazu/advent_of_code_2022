from pathlib import Path
from typing import NamedTuple

import more_itertools as mit

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines


class Range(NamedTuple):
    start: int
    end: int


def parse_line(line: str) -> tuple[Range, Range]:
    left, right = line.split(",")
    left_start, left_end = map(int, left.split("-"))
    right_start, right_end = map(int, right.split("-"))
    return Range(start=left_start, end=left_end), Range(
        start=right_start, end=right_end
    )


def is_subset(superset: Range, subset: Range) -> bool:
    return superset.start <= subset.start and subset.end <= superset.end


def is_overlapping(pair: tuple[Range, Range]) -> bool:
    left, right = pair
    return is_subset(left, right) or is_subset(right, left)


@wrap_main
def main(filename: Path) -> str:
    lines = get_stripped_lines(filename)
    ranges = map(parse_line, lines)
    overlapping_ranges = filter(is_overlapping, ranges)
    count = mit.ilen(overlapping_ranges)
    return str(count)


if __name__ == "__main__":
    main()
