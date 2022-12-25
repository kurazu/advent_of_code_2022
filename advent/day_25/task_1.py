import logging
from pathlib import Path
from typing import Iterable, NewType

import pytest

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines
from ..logs import setup_logging

logger = logging.getLogger(__name__)


SNAFU = NewType("SNAFU", str)


def get_numbers(filename: Path) -> Iterable[SNAFU]:
    return map(SNAFU, get_stripped_lines(filename))


DIGITS = {
    "2": 2,
    "1": 1,
    "0": 0,
    "-": -1,
    "=": -2,
}


def snafu_to_int(snafu: SNAFU) -> int:
    value = 0
    for pow, digit in enumerate(reversed(snafu)):
        value += DIGITS[digit] * 5**pow
    return value


def int_to_snafu(number: int) -> SNAFU:
    snafu_digits: list[str] = []
    carry = 0
    while number != 0:
        remainder = number % 5 + carry
        if remainder in {0, 1, 2}:
            snafu_digits.append(str(remainder))
            carry = 0
        elif remainder == 3:
            snafu_digits.append("=")
            carry = 1
        elif remainder == 4:
            snafu_digits.append("-")
            carry = 1
        number //= 5
    if carry != 0:
        snafu_digits.append(str(carry))
    return SNAFU("".join(reversed(snafu_digits)))


TEST_SAMPLES: list[tuple[int, SNAFU]] = [
    (1, SNAFU("1")),
    (2, SNAFU("2")),
    (3, SNAFU("1=")),
    (4, SNAFU("1-")),
    (5, SNAFU("10")),
    (6, SNAFU("11")),
    (7, SNAFU("12")),
    (8, SNAFU("2=")),
    (9, SNAFU("2-")),
    (10, SNAFU("20")),
    (15, SNAFU("1=0")),
    (20, SNAFU("1-0")),
    (2022, SNAFU("1=11-2")),
    (12345, SNAFU("1-0---0")),
    (314159265, SNAFU("1121-1110-1=0")),
]


@pytest.mark.parametrize("number,snafu", TEST_SAMPLES)
def test_snafu_to_int(number: int, snafu: SNAFU) -> None:
    assert snafu_to_int(snafu) == number


@pytest.mark.parametrize("number,snafu", TEST_SAMPLES)
def test_int_to_snafu(number: int, snafu: SNAFU) -> None:
    assert int_to_snafu(number) == snafu


@wrap_main
def main(filename: Path) -> str:
    snafus = get_numbers(filename)
    numbers = map(snafu_to_int, snafus)
    total = sum(numbers)
    logger.debug("Total in decimal: %d", total)
    return int_to_snafu(total)


if __name__ == "__main__":
    setup_logging()
    main()
