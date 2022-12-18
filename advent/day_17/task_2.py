import logging
from pathlib import Path

from ..cli_utils import wrap_main
from ..logs import setup_logging
from .task_1 import Simulator, _visualize_board, get_directions

logger = logging.getLogger(__name__)


@wrap_main
def main(filename: Path) -> str:
    directions = get_directions(filename)
    simulator = Simulator(directions)
    steps = 1000000000000
    height = simulator.simulate(steps)
    logger.info(
        "Board after %s steps:\n%s", steps, _visualize_board(simulator.board[-50:])
    )
    return str(height)


if __name__ == "__main__":
    setup_logging(logging.WARNING)
    main()
