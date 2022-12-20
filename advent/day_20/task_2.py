import logging
from pathlib import Path

import tqdm

from ..cli_utils import wrap_main
from ..logs import setup_logging
from .task_1 import fast_forward, find_value, mix, read_numbers, to_linked_list

logger = logging.getLogger(__name__)


@wrap_main
def main(filename: Path) -> str:
    decryption_key = 811589153
    numbers = read_numbers(filename)
    numbers = map(lambda n: n * decryption_key, numbers)
    nodes_in_order = to_linked_list(numbers)

    for _ in tqdm.trange(10):
        mix(nodes_in_order)

    zero_node = find_value(nodes_in_order[0], 0)
    logger.debug("Zero node: %r", zero_node)

    node1000 = fast_forward(zero_node, 1000)
    logger.info("Node after 1000 steps: %d", node1000.value)
    node2000 = fast_forward(node1000, 1000)
    logger.info("Node after 2000 steps: %d", node2000.value)
    node3000 = fast_forward(node2000, 1000)
    logger.info("Node after 3000 steps: %d", node3000.value)
    total = node1000.value + node2000.value + node3000.value
    return str(total)


if __name__ == "__main__":
    setup_logging(logging.INFO)
    main()
