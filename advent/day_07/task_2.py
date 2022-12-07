from pathlib import Path

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines
from .task_1 import construct_tree, find_dirs


@wrap_main
def main(filename: Path) -> str:
    max_space = 70000000
    required_space = 30000000
    lines = list(get_stripped_lines(filename))
    tree = construct_tree(lines)
    currently_unused = max_space - tree.size
    to_free = required_space - currently_unused
    all_dirs = find_dirs(tree)
    matching_dirs = filter(lambda dir: dir.size >= to_free, all_dirs)
    dir_to_delete = min(matching_dirs, key=lambda dir: dir.size)
    return str(dir_to_delete.size)


if __name__ == "__main__":
    main()
