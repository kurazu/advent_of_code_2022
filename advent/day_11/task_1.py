import heapq
import logging
import operator
import re
from dataclasses import dataclass, field
from functools import reduce
from pathlib import Path
from typing import NewType, Protocol

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines
from ..logs import setup_logging

logger = logging.getLogger(__name__)

MonkeyId = NewType("MonkeyId", int)
WorryLevel = NewType("WorryLevel", int)


class Operation(Protocol):
    def __call__(self, old: WorryLevel) -> WorryLevel:
        ...


@dataclass
class Addition:
    operand: int

    def __call__(self, old: WorryLevel) -> WorryLevel:
        return WorryLevel(old + self.operand)


@dataclass
class Multiplication:
    operand: int

    def __call__(self, old: WorryLevel) -> WorryLevel:
        return WorryLevel(old * self.operand)


@dataclass
class Square:
    def __call__(self, old: WorryLevel) -> WorryLevel:
        return WorryLevel(old**2)


@dataclass
class Monkey:
    items: list[WorryLevel]
    operation: Operation
    test_divisible_by: WorryLevel
    target_monkey_true: MonkeyId
    target_monkey_false: MonkeyId
    inspected_items: int = field(default=0, init=False)


monkey_pattern = re.compile(r"^Monkey (?P<monkey_id>\d+)\:$")
starting_items_pattern = re.compile(
    r"^  Starting items\: (?P<starting_items>\d+(, \d+)*)$"
)
operation_pattern = re.compile(
    r"^  Operation\: new \= old (?P<operator>[\+\*]) (?P<operand>(\d+|old))$"
)
test_pattern = re.compile(r"^  Test\: divisible by (?P<test_divisible_by>\d+)$")
true_pattern = re.compile(r"^    If true\: throw to monkey (?P<monkey_id>\d+)$")
false_pattern = re.compile(r"^    If false\: throw to monkey (?P<monkey_id>\d+)$")


def parse_id(line: str) -> MonkeyId:
    match = monkey_pattern.match(line)
    assert match is not None, line
    return MonkeyId(int(match.group("monkey_id")))


def parse_starting_items(line: str) -> list[WorryLevel]:
    match = starting_items_pattern.match(line)
    assert match is not None, line
    return [WorryLevel(int(item)) for item in match.group("starting_items").split(", ")]


def parse_operation(line: str) -> Operation:
    match = operation_pattern.match(line)
    assert match is not None, line
    operator = match.group("operator")
    operand = match.group("operand")
    if operator == "+":
        return Addition(int(operand))
    elif operator == "*" and operand == "old":
        return Square()
    else:
        assert operator == "*"
        return Multiplication(int(operand))


def parse_divisible_by(line: str) -> WorryLevel:
    match = test_pattern.match(line)
    assert match is not None, line
    return WorryLevel(int(match.group("test_divisible_by")))


def parse_target_true(line: str) -> MonkeyId:
    match = true_pattern.match(line)
    assert match is not None, line
    return MonkeyId(int(match.group("monkey_id")))


def parse_target_false(line: str) -> MonkeyId:
    match = false_pattern.match(line)
    assert match is not None, line
    return MonkeyId(int(match.group("monkey_id")))


def parse_monkeys(filename: Path) -> dict[MonkeyId, Monkey]:
    monkeys: dict[MonkeyId, Monkey] = {}
    lines = iter(get_stripped_lines(filename))
    while True:
        try:
            line = next(lines)
        except StopIteration:
            break
        if not line:
            continue

        monkey_id = parse_id(line)
        starting_items = parse_starting_items(next(lines))
        operation = parse_operation(next(lines))
        test_divisible_by = parse_divisible_by(next(lines))
        target_monkey_true = parse_target_true(next(lines))
        target_monkey_false = parse_target_false(next(lines))

        monkeys[monkey_id] = Monkey(
            items=starting_items,
            operation=operation,
            test_divisible_by=test_divisible_by,
            target_monkey_true=target_monkey_true,
            target_monkey_false=target_monkey_false,
        )

    return monkeys


def play_round(monkeys: dict[MonkeyId, Monkey]) -> None:
    for monkey_id, monkey in monkeys.items():
        logger.info("Monkey %d", monkey_id)
        while monkey.items:
            item = monkey.items.pop()
            monkey.inspected_items += 1
            new = monkey.operation(item)
            new = WorryLevel(new // 3)
            if new % monkey.test_divisible_by == 0:
                target_monkey = monkey.target_monkey_true
            else:
                target_monkey = monkey.target_monkey_false
            monkeys[target_monkey].items.append(new)


@wrap_main
def main(filename: Path) -> str:
    monkeys = parse_monkeys(filename)
    for round in range(1, 20 + 1):
        logger.debug("Round %d", round)
        play_round(monkeys)
    logger.debug("Finished")
    inspected = (monkey.inspected_items for monkey in monkeys.values())
    best_two = heapq.nlargest(2, inspected)
    score = reduce(operator.mul, best_two)
    return str(score)


if __name__ == "__main__":
    setup_logging()
    main()
