import operator
import re
from pathlib import Path
from typing import Iterator, NamedTuple

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines

pattern = re.compile(r"^move (?P<count>\d+) from (?P<from>\d) to (?P<to>\d)$")


def parse_stacks(input_lines: Iterator[str]) -> list[list[str]]:
    config_lines: list[str] = []

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

    return stacks


class Instruction(NamedTuple):
    count: int
    from_: int
    to: int


def parse_instructions(input_lines: Iterator[str]) -> Iterator[Instruction]:
    for instruction_line in input_lines:
        match = pattern.match(instruction_line)
        assert match is not None, f"{instruction_line!r}"
        count = int(match.group("count"))
        from_ = int(match.group("from")) - 1
        to = int(match.group("to")) - 1
        yield Instruction(count=count, from_=from_, to=to)


@wrap_main
def main(filename: Path) -> str:
    input_lines = iter(get_stripped_lines(filename))
    stacks = parse_stacks(input_lines)
    for instruction in parse_instructions(input_lines):
        source_stack = stacks[instruction.from_]
        target_stack = stacks[instruction.to]
        for _ in range(instruction.count):
            target_stack.append(source_stack.pop())

    return "".join(map(operator.itemgetter(-1), stacks))


if __name__ == "__main__":
    main()
