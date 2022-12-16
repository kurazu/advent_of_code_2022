import itertools as it
import logging
from pathlib import Path

import tqdm

from ..cli_utils import wrap_main
from ..logs import setup_logging
from .task_1 import Graph, parse_graph

logger = logging.getLogger(__name__)


def calculate_distances(graph: Graph) -> dict[str, dict[str, int]]:
    distances: dict[str, dict[str, int]] = {}

    all_nodes = set(graph.nodes)

    def _calculate_distances(node: str) -> dict[str, int]:
        visited: set[str] = set()
        costs: dict[str, int] = {node: 0}

        while len(visited) != len(all_nodes):
            lowest_unvisited_node = min(
                it.filterfalse(visited.__contains__, costs), key=costs.get
            )
            unvisited_neighbours = set(graph.edges[lowest_unvisited_node]) - visited
            for neighbour in unvisited_neighbours:
                costs[neighbour] = costs[lowest_unvisited_node] + 1
            visited.add(lowest_unvisited_node)

        return costs

    for node in tqdm.tqdm(all_nodes, desc="Calculating distances"):
        distances[node] = _calculate_distances(node)
    return distances


def dfs(graph: Graph, *, time: int) -> int:
    distances = calculate_distances(graph)
    breakpoint()
    return 0
    cache: dict[tuple[frozenset[str], str, str, bool, int], int] = {}

    def _dfs(
        *,
        opened: frozenset[str],
        current_you: str,
        current_elephant: str,
        your_turn: bool,
        remaining_time: int
    ) -> int:
        if remaining_time == 0:
            return 0
        key = (opened, current_you, current_elephant, your_turn, remaining_time)
        if key in cache:
            return cache[key]
        # at each step we taka a decision: either we open a new value or we move
        new_remaining_time = remaining_time if your_turn else (remaining_time - 1)
        possible_scores: list[int] = [0]
        current = current_you if your_turn else current_elephant
        can_open_current_valve = current not in opened and graph.nodes[current] > 0
        if can_open_current_valve:
            current_throughput = graph.nodes[current]
            open_score = (
                _dfs(
                    opened=opened | {current},
                    current_you=current_you,
                    current_elephant=current_elephant,
                    your_turn=not your_turn,
                    remaining_time=new_remaining_time,
                )
                + (remaining_time - 1) * current_throughput
            )
            possible_scores.append(open_score)
        possible_destinations = graph.edges[current]
        for destination in possible_destinations:
            move_score = _dfs(
                opened=opened,
                current_you=destination if your_turn else current_you,
                current_elephant=destination if not your_turn else current_elephant,
                your_turn=not your_turn,
                remaining_time=new_remaining_time,
            )
            possible_scores.append(move_score)
        best_score = cache[key] = max(possible_scores)
        return best_score

    return _dfs(
        opened=frozenset(),
        current_you="AA",
        current_elephant="AA",
        your_turn=True,
        remaining_time=time,
    )


@wrap_main
def main(filename: Path) -> str:
    graph = parse_graph(filename)
    best_score = dfs(graph, time=26)
    return str(best_score)


if __name__ == "__main__":
    setup_logging()
    main()
