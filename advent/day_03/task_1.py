from pathlib import Path

import click

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines


def get_common_item(all_items: str) -> str:
    total_items = len(all_items)
    assert total_items % 2 == 0
    half_items = total_items // 2
    left_items = all_items[:half_items]
    right_items = all_items[half_items:]
    assert len(left_items) == len(right_items)
    left_set = set(left_items)
    right_set = set(right_items)
    common_set = left_set & right_set
    assert len(common_set) == 1
    (common_item,) = common_set
    return common_item


def get_priority(item: str) -> int:
    char_code = ord(item)
    if "a" <= item <= "z":
        return char_code - ord("a") + 1
    elif "A" <= item <= "Z":
        return char_code - ord("A") + 27
    else:
        raise ValueError(item)


@wrap_main
def main(filename: Path) -> None:
    lines = get_stripped_lines(filename)
    common_items = map(get_common_item, lines)
    priorities = map(get_priority, common_items)
    total_priority = sum(priorities)
    click.echo(total_priority)


if __name__ == "__main__":
    main()
