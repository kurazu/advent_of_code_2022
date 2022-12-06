from pathlib import Path

import click
import more_itertools as mit
import pytest

from ..cli_utils import wrap_main


def find_position(text: str) -> int:
    return 0


@wrap_main
def main(filename: Path) -> str:
    with filename.open() as f:
        text = f.read().strip()
    position = find_position(text)
    click.echo(position)


TEST_CASES: list[tuple[str, int]] = [
    ("mjqjpqmgbljsphdztnvjfqwrcgsmlb", 7),
    ("bvwbjplbgvbhsrlpgdmjqwftvncz", 5),
    ("nppdvjthqldpwncqszvftbrmjlhg", 6),
    ("nznrnfrfntjfmvfwmzdfjlvtqnbhcprsg", 10),
    ("zcfzfwzzqfrljwzlrfnpqdbhtmscgvjw", 11),
]


@pytest.mark.parametrize("text, expected", TEST_CASES)
def test_find_position(text: str, expected: int) -> None:
    assert find_position(text) == expected


if __name__ == "__main__":
    main()
