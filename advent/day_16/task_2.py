import itertools as it
import logging
from pathlib import Path

from ..cli_utils import wrap_main
from ..logs import setup_logging
from .task_1 import Graph, calculate_distances, get_possible_moves, parse_graph

logger = logging.getLogger(__name__)


def dfs(graph: Graph, *, time: int) -> int:
    distances = calculate_distances(graph)
    cache: dict[tuple[frozenset[str], str, str, int, int], int] = {}

    # it only makes sense to open valves that have a positive throughput
    all_working_nodes = frozenset(
        node for node, throughput in graph.nodes.items() if throughput > 0
    )

    def _dfs(
        *,
        opened: frozenset[str],
        current_you: str,
        current_elephant: str,
        remaining_time_you: int,
        remaining_time_elephant: int
    ) -> int:
        key = (
            opened,
            current_you,
            current_elephant,
            remaining_time_you,
            remaining_time_elephant,
        )
        if key in cache:
            return cache[key]
        # determine which valves are left to be opened
        your_possible_valves = get_possible_moves(
            throughputs=graph.nodes,
            all_working_nodes=all_working_nodes,
            opened=opened,
            distances_from_current=distances[current_you],
            remaining_time=remaining_time_you,
        )
        total_rewards: list[int] = []
        for you_valve in your_possible_valves:
            elefant_possible_valves = get_possible_moves(
                throughputs=graph.nodes,
                all_working_nodes=all_working_nodes,
                opened=opened | {you_valve.node},
                distances_from_current=distances[current_elephant],
                remaining_time=remaining_time_elephant,
            )
            total_rewards.append(
                you_valve.reward
                + _dfs(
                    opened=opened | {you_valve.node},
                    current_you=you_valve.node,
                    current_elephant=current_elephant,
                    remaining_time_you=remaining_time_you - you_valve.cost,
                    remaining_time_elephant=remaining_time_elephant,
                )
            )
            for elefant_valve in elefant_possible_valves:
                total_rewards.append(
                    you_valve.reward
                    + elefant_valve.reward
                    + _dfs(
                        opened=opened | {you_valve.node, elefant_valve.node},
                        current_you=you_valve.node,
                        current_elephant=elefant_valve.node,
                        remaining_time_you=remaining_time_you - you_valve.cost,
                        remaining_time_elephant=remaining_time_elephant
                        - elefant_valve.cost,
                    )
                )
        best_reward = cache[key] = max(total_rewards, default=0)

        return best_reward

    return _dfs(
        opened=frozenset(),
        current_you="AA",
        current_elephant="AA",
        remaining_time_you=time,
        remaining_time_elephant=time,
    )


@wrap_main
def main(filename: Path) -> str:
    graph = parse_graph(filename)
    best_score = dfs(graph, time=26)
    return str(best_score)


if __name__ == "__main__":
    setup_logging()
    main()
