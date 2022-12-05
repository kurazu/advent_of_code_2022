import operator
from pathlib import Path

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines
from .task_1 import parse_instructions, parse_stacks


@wrap_main
def main(filename: Path) -> str:
    input_lines = iter(get_stripped_lines(filename))
    stacks = parse_stacks(input_lines)
    for instruction in parse_instructions(input_lines):
        source_stack = stacks[instruction.from_]
        target_stack = stacks[instruction.to]
        lifted: list[str] = []
        for _ in range(instruction.count_):
            lifted.append(source_stack.pop())
        target_stack.extend(reversed(lifted))

    return "".join(map(operator.itemgetter(-1), stacks))


if __name__ == "__main__":
    main()
