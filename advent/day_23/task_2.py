import itertools as it
import logging
from pathlib import Path

from ..cli_utils import wrap_main
from ..logs import setup_logging
from .task_1 import get_checks, read_board, simulate

logger = logging.getLogger(__name__)


@wrap_main
def main(filename: Path) -> str:
    elves = set(read_board(filename))
    checks = iter(get_checks())
    for round in it.count(1):
        round_checks = next(checks)
        new_elves = simulate(elves, round_checks)
        if new_elves == elves:
            break
        elves = new_elves
    return str(round)


if __name__ == "__main__":
    setup_logging()
    main()
