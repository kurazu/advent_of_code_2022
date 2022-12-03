import functools
import operator
from pathlib import Path

import more_itertools as mit

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines
from .task_1 import get_priority


def find_common_item(group: list[set[str]]) -> str:
    common_items = functools.reduce(operator.and_, group)
    assert len(common_items) == 1
    (common_item,) = common_items
    return common_item


@wrap_main
def main(filename: Path) -> str:
    lines = get_stripped_lines(filename)
    sets = map(set, lines)
    groups = mit.batched(sets, 3)
    common_items = map(find_common_item, groups)
    priorities = map(get_priority, common_items)
    total_priority = sum(priorities)
    return str(total_priority)


if __name__ == "__main__":
    main()
