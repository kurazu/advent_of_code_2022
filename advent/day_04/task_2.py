from pathlib import Path
from typing import NamedTuple

import more_itertools as mit

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines
from .task_1 import Range, parse_line


def is_overlapping(pair: tuple[Range, Range]) -> bool:
    left, right = pair
    if left.start <= right.start <= left.end:
        return True
    elif right.start <= left.start <= right.end:
        return True
    else:
        return False


@wrap_main
def main(filename: Path) -> str:
    lines = get_stripped_lines(filename)
    ranges = map(parse_line, lines)
    overlapping_ranges = filter(is_overlapping, ranges)
    count = mit.ilen(overlapping_ranges)
    return str(count)


if __name__ == "__main__":
    main()
