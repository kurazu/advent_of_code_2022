import itertools as it
import logging
from pathlib import Path
from typing import Iterable

import more_itertools as mit

from .. import __name__ as package_name
from ..cli_utils import wrap_main
from .task_1 import (
    Instruction,
    Position,
    apply_instruction,
    parse_instructions,
    tail_catchup,
    visualize_visited_locations,
)

logger = logging.getLogger(__name__)


def execute_instructions(
    instructions: Iterable[Instruction], n_knots: int = 10
) -> set[Position]:
    head = Position(0, 0)
    knots = [Position(0, 0) for _ in range(n_knots - 1)]
    tail_visited_locations = {knots[-1]}
    # visualize_visited_locations(
    #     tail_visited_locations, head=head_location, tail=tail_location
    # )
    for instruction in instructions:
        logger.debug("Processing instruction %s", instruction)
        for step in range(instruction.distance):
            logger.debug("Step %d of instruction %s", step + 1, instruction)
            head = apply_instruction(head, instruction.direction)
            new_knots: list[Position] = []
            preceeding = head
            for following in knots:
                preceeding = tail_catchup(following, preceeding)
                new_knots.append(preceeding)

            assert len(new_knots) == len(knots)
            knots = new_knots
            tail_visited_locations.add(knots[-1])
            # visualize_visited_locations(
            #     tail_visited_locations, head=head_location, tail=tail_location
            # )
        logger.debug("Finished instruction %s", instruction)
    return tail_visited_locations


@wrap_main
def main(filename: Path) -> str:
    instructions = parse_instructions(filename)
    visited_locations = execute_instructions(instructions)
    logger.info("Finished")
    visualize_visited_locations(visited_locations)
    return str(len(visited_locations))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.WARNING,
        format="[%(asctime)s][%(levelname)8s][%(name)s] %(message)s",
    )
    logging.getLogger(package_name).setLevel(logging.DEBUG)
    logger.setLevel(logging.DEBUG)
    main()
