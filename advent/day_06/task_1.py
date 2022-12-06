from pathlib import Path

import more_itertools as mit
import pytest

from ..cli_utils import wrap_main


def find_position(text: str, window_size: int = 4) -> int:
    for idx, window in enumerate(mit.sliding_window(text, window_size)):
        if len(set(window)) == window_size:
            return idx + window_size
    raise AssertionError("Marker not found")


@wrap_main
def main(filename: Path) -> str:
    with filename.open() as f:
        text = f.read().strip()
    position = find_position(text)
    return str(position)


TEST_CASES: list[tuple[str, int, int]] = [
    ("mjqjpqmgbljsphdztnvjfqwrcgsmlb", 4, 7),
    ("bvwbjplbgvbhsrlpgdmjqwftvncz", 4, 5),
    ("nppdvjthqldpwncqszvftbrmjlhg", 4, 6),
    ("nznrnfrfntjfmvfwmzdfjlvtqnbhcprsg", 4, 10),
    ("zcfzfwzzqfrljwzlrfnpqdbhtmscgvjw", 4, 11),
    ("mjqjpqmgbljsphdztnvjfqwrcgsmlb", 14, 19),
    ("bvwbjplbgvbhsrlpgdmjqwftvncz", 14, 23),
    ("nppdvjthqldpwncqszvftbrmjlhg", 14, 23),
    ("nznrnfrfntjfmvfwmzdfjlvtqnbhcprsg", 14, 29),
    ("zcfzfwzzqfrljwzlrfnpqdbhtmscgvjw", 14, 26),
]


@pytest.mark.parametrize("text, window_size, expected", TEST_CASES)
def test_find_position(text: str, window_size: int, expected: int) -> None:
    assert find_position(text, window_size) == expected


def test_find_position_no_marker() -> None:
    with pytest.raises(AssertionError, match="Marker not found"):
        find_position("abcabcabcabc")


if __name__ == "__main__":
    main()
