import logging
from pathlib import Path

from ..cli_utils import wrap_main
from ..logs import setup_logging
from .task_1 import Monkey, MonkeyId, OperationMonkey, SimpleMonkey, parse_monkeys

logger = logging.getLogger(__name__)

ROOT_ID = MonkeyId("root")
HUMAN_ID = MonkeyId("humn")


class HumanFound(Exception):
    pass


def resolve(monkeys: dict[MonkeyId, Monkey], monkey: Monkey) -> int:
    dependencies = monkey.dependencies
    if HUMAN_ID in dependencies:
        raise HumanFound()
    dep_results = {dep: resolve(monkeys, monkeys[dep]) for dep in dependencies}
    return monkey(dep_results)


def propagate(monkeys: dict[MonkeyId, Monkey], monkey: Monkey, value: int) -> None:
    # see if left branch can be resolved
    if isinstance(monkey, SimpleMonkey):
        logger.debug(
            "Monkey is simple, setting result from %d to %d", monkey.result, value
        )
        monkey.result = value
        return
    assert isinstance(monkey, OperationMonkey)
    left = monkeys[monkey.left]
    right = monkeys[monkey.right]
    to_propage: Monkey | None = None
    left_value: int | None
    right_value: int | None
    try:
        if monkey.left == HUMAN_ID:
            raise HumanFound()
        left_value = resolve(monkeys, left)
    except HumanFound:
        left_value = None
        to_propage = left
    try:
        if monkey.right == HUMAN_ID:
            raise HumanFound()
        right_value = resolve(monkeys, right)
    except HumanFound:
        right_value = None
        to_propage = right

    assert to_propage is not None
    assert (left_value is not None) ^ (right_value is not None)

    new_value = monkey.inverse_operator(value, left_value, right_value)
    propagate(monkeys, to_propage, new_value)


@wrap_main
def main(filename: Path) -> str:
    monkeys = parse_monkeys(filename)
    root_monkey = monkeys[ROOT_ID]
    assert isinstance(root_monkey, OperationMonkey)
    left = monkeys[root_monkey.left]
    right = monkeys[root_monkey.right]
    calculated: int
    to_process: Monkey
    try:
        calculated = resolve(monkeys, left)
    except HumanFound:
        calculated = resolve(monkeys, right)
        to_process = left
    else:
        to_process = right

    propagate(monkeys, to_process, calculated)
    human_monkey = monkeys[HUMAN_ID]
    assert isinstance(human_monkey, SimpleMonkey)
    return str(human_monkey.result)


if __name__ == "__main__":
    setup_logging()
    main()
