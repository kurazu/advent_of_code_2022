import operator
import re
from pathlib import Path

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines

pattern = re.compile(r"^move (?P<count>\d+) from (?P<from>\d) to (?P<to>\d)$")


@wrap_main
def main(filename: Path) -> str:
    config_lines: list[str] = []
    input_lines = iter(get_stripped_lines(filename))
    while line := next(input_lines):
        config_lines.append(line)
    numbers_line = config_lines.pop().strip()
    numbers = numbers_line.split("  ")
    length = len(numbers)
    stacks: list[list[str]] = [[] for _ in range(length)]
    while config_lines:
        line = config_lines.pop()
        for idx in range(length):
            try:
                crate = line[idx * 4 + 1]
            except IndexError:
                crate = " "
            if crate != " ":
                stacks[idx].append(crate)

    for instruction_line in input_lines:
        match = pattern.match(instruction_line)
        assert match is not None, f"{instruction_line!r}"
        count = int(match.group("count"))
        from_ = int(match.group("from")) - 1
        to = int(match.group("to")) - 1
        source_stack = stacks[from_]
        target_stack = stacks[to]
        for _ in range(count):
            target_stack.append(source_stack.pop())

    return "".join(map(operator.itemgetter(-1), stacks))


if __name__ == "__main__":
    main()
