import graphlib
import logging
import operator
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, NewType, Protocol

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines
from ..logs import setup_logging

logger = logging.getLogger(__name__)
MonkeyId = NewType("MonkeyId", str)


class Monkey(Protocol):
    @property
    def dependencies(self) -> frozenset[MonkeyId]:
        ...

    def __call__(self, previous_results: dict[MonkeyId, int]) -> int:
        ...


EMPTY: frozenset[MonkeyId] = frozenset()


@dataclass
class SimpleMonkey:
    result: int
    dependencies: frozenset[MonkeyId] = field(default=EMPTY, init=False)

    def __call__(self, previous_results: dict[MonkeyId, int]) -> int:
        return self.result


InverseOperatorType = Callable[[int, int | None, int | None], int]


@dataclass
class OperationMonkey:
    left: MonkeyId
    right: MonkeyId
    operator: Callable[[int, int], int]
    inverse_operator: InverseOperatorType

    @property
    def dependencies(self) -> frozenset[MonkeyId]:
        return frozenset([self.left, self.right])

    def __call__(self, previous_results: dict[MonkeyId, int]) -> int:
        left_result = previous_results[self.left]
        right_result = previous_results[self.right]
        return self.operator(left_result, right_result)


simple_pattern = re.compile(r"^(?P<monkey_id>\w{4})\: (?P<result>\d+)$")
operation_pattern = re.compile(
    r"^(?P<monkey_id>\w{4})\: "
    r"(?P<left>\w{4}) (?P<operator>[\+\-\*\/]) (?P<right>\w{4})$"
)

SYMBOL_TO_OPERATOR: dict[str, Callable[[int, int], int]] = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.floordiv,
}


def inverse_plus(result: int, left: int | None, right: int | None) -> int:
    if right is None:
        assert left is not None
        return result - left
    else:
        return result - right


def inverse_minus(result: int, left: int | None, right: int | None) -> int:
    if right is None:
        assert left is not None
        return left - result
    else:
        return result + right


def inverse_mul(result: int, left: int | None, right: int | None) -> int:
    if right is None:
        assert left is not None
        return result // left
    else:
        return result // right


def inverse_div(result: int, left: int | None, right: int | None) -> int:
    if right is None:
        assert left is not None
        return left // result
    else:
        return result * right


SYMBOL_TO_INVERSE_OPERATOR: dict[str, InverseOperatorType] = {
    "+": inverse_plus,
    "-": inverse_minus,
    "*": inverse_mul,
    "/": inverse_div,
}


def parse_monkeys(filename: Path) -> dict[MonkeyId, Monkey]:
    monkeys = {}
    for line in get_stripped_lines(filename):
        monkey_id: MonkeyId
        monkey: Monkey
        if (match := simple_pattern.match(line)) is not None:
            monkey_id = MonkeyId(match.group("monkey_id"))
            result = int(match.group("result"))
            monkey = SimpleMonkey(result=result)
        elif (match := operation_pattern.match(line)) is not None:
            monkey_id = MonkeyId(match.group("monkey_id"))
            left = MonkeyId(match.group("left"))
            right = MonkeyId(match.group("right"))
            operator = SYMBOL_TO_OPERATOR[match.group("operator")]
            inverse_operator = SYMBOL_TO_INVERSE_OPERATOR[match.group("operator")]
            monkey = OperationMonkey(
                left=left,
                right=right,
                operator=operator,
                inverse_operator=inverse_operator,
            )
        monkeys[monkey_id] = monkey
    return monkeys


def topological_sort(monkeys: dict[MonkeyId, Monkey]) -> Iterable[MonkeyId]:
    graph: dict[MonkeyId, set[MonkeyId]] = defaultdict(set)
    for monkey_id, monkey in monkeys.items():
        for dependency in monkey.dependencies:
            graph[monkey_id].add(dependency)
    sorter = graphlib.TopologicalSorter(graph=graph)
    return sorter.static_order()


@wrap_main
def main(filename: Path) -> str:
    monkeys = parse_monkeys(filename)
    results: dict[MonkeyId, int] = {}
    for monkey_id in topological_sort(monkeys):
        monkey = monkeys[monkey_id]
        results[monkey_id] = monkey(results)
    root_result = results[MonkeyId("root")]
    return str(root_result)


if __name__ == "__main__":
    setup_logging()
    main()
