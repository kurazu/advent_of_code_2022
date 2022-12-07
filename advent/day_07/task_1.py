from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines


@dataclass
class Dir:
    subdirs: dict[str, Dir] = field(default_factory=dict, init=False)
    files: dict[str, int] = field(default_factory=dict, init=False)

    @property
    def size(self) -> int:
        return sum(self.files.values()) + sum(dir.size for dir in self.subdirs.values())


def process_dir(current: Dir, lines: list[str]) -> None:
    while lines:
        line = lines.pop(0)
        if line == "$ cd ..":
            return
        elif line.startswith("$ cd "):
            dir_name = line[5:]
            new_dir = Dir()
            current.subdirs[dir_name] = new_dir
            process_dir(new_dir, lines)
        elif line == "$ ls":
            while lines and not lines[0].startswith("$"):
                line = lines.pop(0)
                type_size, name = line.split(" ", 1)
                if type_size == "dir":
                    continue
                else:
                    size = int(type_size)
                    current.files[name] = size
        else:
            raise AssertionError(line)


def construct_tree(lines: list[str]) -> Dir:
    first_line = lines.pop(0)
    assert first_line == "$ cd /"
    root = Dir()
    process_dir(root, lines)
    return root


def find_dirs(root: Dir) -> Iterator[Dir]:
    yield root
    for subdir in root.subdirs.values():
        yield from find_dirs(subdir)

@wrap_main
def main(filename: Path) -> str:
    lines = list(get_stripped_lines(filename))
    tree = construct_tree(lines)
    small_dirs = filter(lambda dir: dir.size <= 100000, find_dirs(tree))
    total = sum(dir.size for dir in small_dirs)
    return str(total)


if __name__ == "__main__":
    main()
