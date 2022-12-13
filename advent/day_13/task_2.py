import collections
import graphlib
import itertools as it
import logging
import math
import operator
from pathlib import Path

import tqdm

from ..cli_utils import wrap_main
from ..logs import setup_logging
from .task_1 import have_correct_order, read_pairs

logger = logging.getLogger(__name__)


@wrap_main
def main(filename: Path) -> str:
    logger.debug("Reading pairs from %s", filename)
    pairs = read_pairs(filename)
    divider_packets = [[[2]], [[6]]]
    packets = it.chain(divider_packets, it.chain.from_iterable(pairs))
    nodes = dict(enumerate(packets))
    logger.debug("Constructing graph from %d nodes", len(nodes))
    graph: dict[int, set[int]] = collections.defaultdict(set)
    a_key: int
    b_key: int
    for a_key, b_key in tqdm.tqdm(
        it.combinations(nodes, 2), total=math.comb(len(nodes), 2)
    ):
        a = nodes[a_key]
        b = nodes[b_key]
        if have_correct_order(a, b):
            graph[b_key].add(a_key)
        else:
            graph[a_key].add(b_key)

    logger.debug("Sorting graph")
    sorter = graphlib.TopologicalSorter(graph=graph)
    divider_indicies: list[int] = []
    for idx, key in enumerate(sorter.static_order(), 1):
        if key in {0, 1}:  # the divider packets were top of the list
            divider_indicies.append(idx)
    assert len(divider_indicies) == 2
    return str(operator.mul(*divider_indicies))


if __name__ == "__main__":
    setup_logging(logging.INFO)
    main()
