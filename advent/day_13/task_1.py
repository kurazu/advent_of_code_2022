import json
import logging
from pathlib import Path
from typing import Any, Iterable

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines
from ..logs import setup_logging

logger = logging.getLogger(__name__)


def read_pairs(filename: Path) -> Iterable[tuple[list[Any], list[Any]]]:
    lines = iter(get_stripped_lines(filename))
    while True:
        try:
            line = next(lines)
        except StopIteration:
            break
        if not line:
            continue
        first = json.loads(line)
        assert isinstance(first, list)
        second = json.loads(next(lines))
        assert isinstance(second, list)
        yield first, second


def has_correct_order(left: list[Any], right: list[Any]) -> bool:
    breakpoint()
    return 0


@wrap_main
def main(filename: Path) -> str:
    pairs = read_pairs(filename)
    enumerated_pairs = enumerate(pairs, start=1)
    indices_in_correct_order = (
        idx for idx, pair in enumerated_pairs if has_correct_order(*pair)
    )
    sum_of_indicies = sum(indices_in_correct_order)
    return str(sum_of_indicies)


if __name__ == "__main__":
    setup_logging()
    main()
