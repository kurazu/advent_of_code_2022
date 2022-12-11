import heapq
import logging
import operator
import re
from dataclasses import dataclass, field
from functools import reduce
from pathlib import Path
from typing import Callable, NewType, Protocol

import numpy as np
import tqdm
from numpy import typing as npt

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines
from ..logs import setup_logging

logger = logging.getLogger(__name__)

MonkeyId = NewType("MonkeyId", int)


class Operation(Protocol):
    def __call__(self, old: npt.NDArray[np.int64]) -> npt.NDArray[np.int64]:
        ...


@dataclass
class Addition:
    operand: int

    def __call__(self, old: npt.NDArray[np.int64]) -> npt.NDArray[np.int64]:
        return old + self.operand


@dataclass
class Multiplication:
    operand: int

    def __call__(self, old: npt.NDArray[np.int64]) -> npt.NDArray[np.int64]:
        return old * self.operand


@dataclass
class Square:
    def __call__(self, old: npt.NDArray[np.int64]) -> npt.NDArray[np.int64]:
        return old**2


@dataclass
class Monkey:
    items: npt.NDArray[np.int64]
    operation: Operation
    test_divisible_by: int
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


def parse_starting_items(line: str) -> list[int]:
    match = starting_items_pattern.match(line)
    assert match is not None, line
    return [int(item) for item in match.group("starting_items").split(", ")]


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


def parse_divisible_by(line: str) -> int:
    match = test_pattern.match(line)
    assert match is not None, line
    return int(match.group("test_divisible_by"))


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
            items=np.array(starting_items, dtype=np.int64),
            operation=operation,
            test_divisible_by=test_divisible_by,
            target_monkey_true=target_monkey_true,
            target_monkey_false=target_monkey_false,
        )

    return monkeys


EMPTY_ITEMS = np.empty((0,), dtype=np.int64)


def play_round(
    monkeys: dict[MonkeyId, Monkey],
    normalization: Callable[[npt.NDArray[np.int64]], npt.NDArray[np.int64]],
) -> None:
    for monkey_id, monkey in monkeys.items():
        monkey.inspected_items += len(monkey.items)
        new = monkey.operation(monkey.items)
        normalized = normalization(new)
        divisible_mask = (normalized % monkey.test_divisible_by) == 0
        true_items = normalized[divisible_mask]
        false_items = normalized[~divisible_mask]
        true_monkey = monkeys[monkey.target_monkey_true]
        true_monkey.items = np.concatenate([true_monkey.items, true_items])
        false_monkey = monkeys[monkey.target_monkey_false]
        false_monkey.items = np.concatenate([false_monkey.items, false_items])
        monkey.items = EMPTY_ITEMS


def play_rounds(
    monkeys: dict[MonkeyId, Monkey],
    *,
    normalization: Callable[[npt.NDArray[np.int64]], npt.NDArray[np.int64]],
    n_rounds: int
) -> None:
    for round in tqdm.trange(n_rounds):
        play_round(monkeys, normalization=normalization)


@wrap_main
def main(filename: Path) -> str:
    monkeys = parse_monkeys(filename)
    play_rounds(monkeys=monkeys, normalization=lambda x: x // 3, n_rounds=20)
    inspected = (monkey.inspected_items for monkey in monkeys.values())
    best_two = heapq.nlargest(2, inspected)
    score = reduce(operator.mul, best_two)
    return str(score)


if __name__ == "__main__":
    setup_logging()
    main()
