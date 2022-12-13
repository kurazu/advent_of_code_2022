import json
import logging
from itertools import zip_longest
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


def values_have_correct_order(
    left: int | list[Any], right: int | list[Any]
) -> bool | None:
    logger.debug("Comparing %s and %s", left, right)
    if isinstance(left, int) and isinstance(right, int):
        logger.debug("Both items are ints: %s and %s", left, right)
        if left < right:
            logger.debug("Left is less than right: %s < %s", left, right)
            return True
        elif left > right:
            logger.debug("Left is greater than right: %s > %s", left, right)
            return False
        else:
            assert left == right
            logger.debug("Left is equal to right: %s == %s", left, right)
            return None
    elif isinstance(left, list) and isinstance(right, list):
        return lists_have_correct_order(left, right)
    elif isinstance(left, int):
        logger.debug("Left is an int, wrapping: %s", left)
        return values_have_correct_order([left], right)
    else:
        assert isinstance(right, int)
        logger.debug("Right is an int, wrapping: %s", right)
        return values_have_correct_order(left, [right])


missing = object()


def lists_have_correct_order(left: list[Any], right: list[Any]) -> bool | None:
    logger.debug("Comparing lists %s and %s", left, right)

    for left_item, right_item in zip_longest(left, right, fillvalue=missing):
        if left_item is missing:
            return True
        elif right_item is missing:
            return False
        assert isinstance(left_item, (int, list))
        assert isinstance(right_item, (int, list))
        result = values_have_correct_order(left_item, right_item)
        if result is not None:
            return result
    return None


def have_correct_order(left: list[Any], right: list[Any]) -> bool:
    result = lists_have_correct_order(left, right)
    assert result is not None
    return result


@wrap_main
def main(filename: Path) -> str:
    pairs = read_pairs(filename)
    enumerated_pairs = enumerate(pairs, start=1)
    indices_in_correct_order = (
        idx for idx, pair in enumerated_pairs if have_correct_order(*pair)
    )
    sum_of_indicies = sum(indices_in_correct_order)
    return str(sum_of_indicies)


if __name__ == "__main__":
    setup_logging()
    main()
