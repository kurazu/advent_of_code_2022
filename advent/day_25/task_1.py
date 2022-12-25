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
        remainder = (number + carry) % 5
        if remainder in {0, 1, 2}:
            snafu_digits.append(str(remainder))
            carry = 0
        elif remainder == 3:
            snafu_digits.append("=")
            carry = 1
        else:
            assert remainder == 4
            snafu_digits.append("-")
            carry = 1
        number //= 5
    if carry != 0:
        snafu_digits.append(str(carry))
    return SNAFU("".join(reversed(snafu_digits)))


# 1 5 25
TEST_SAMPLES: list[tuple[int, SNAFU]] = [
    (0, SNAFU("0")),
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
    (11, SNAFU("21")),
    (12, SNAFU("22")),
    (13, SNAFU("1==")),
    (14, SNAFU("1=-")),
    (15, SNAFU("1=0")),
    (16, SNAFU("1=1")),
    (17, SNAFU("1=2")),
    (18, SNAFU("1-=")),
    (19, SNAFU("1--")),
    (20, SNAFU("1-0")),
    (21, SNAFU("1-1")),
    (22, SNAFU("1-2")),
    (23, SNAFU("10=")),
    (24, SNAFU("10-")),
    (25, SNAFU("100")),
    (26, SNAFU("101")),
    (27, SNAFU("102")),
    (28, SNAFU("11=")),
    (29, SNAFU("11-")),
    (30, SNAFU("110")),
    (31, SNAFU("111")),
    (32, SNAFU("112")),
    (33, SNAFU("12=")),
    (34, SNAFU("12-")),
    (35, SNAFU("120")),
    (36, SNAFU("121")),
    (37, SNAFU("122")),
    (38, SNAFU("2==")),
    (39, SNAFU("2=-")),
    (40, SNAFU("2=0")),
    (41, SNAFU("2=1")),
    (42, SNAFU("2=2")),
    (43, SNAFU("2-=")),
    (44, SNAFU("2--")),
    (45, SNAFU("2-0")),
    (46, SNAFU("2-1")),
    (47, SNAFU("2-2")),
    (48, SNAFU("20=")),
    (49, SNAFU("20-")),
    (50, SNAFU("200")),
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
