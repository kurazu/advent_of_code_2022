import heapq
import logging
import operator
from functools import reduce
from pathlib import Path

from ..cli_utils import wrap_main
from ..logs import setup_logging
from .task_1 import parse_monkeys, play_rounds

logger = logging.getLogger(__name__)


@wrap_main
def main(filename: Path) -> str:
    monkeys = parse_monkeys(filename)
    play_rounds(monkeys=monkeys, worry_level_drop=1, n_rounds=10_000)
    inspected = (monkey.inspected_items for monkey in monkeys.values())
    best_two = heapq.nlargest(2, inspected)
    score = reduce(operator.mul, best_two)
    return str(score)


if __name__ == "__main__":
    setup_logging()
    main()
