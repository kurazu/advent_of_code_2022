import itertools as it
import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import Iterable, NamedTuple

import tqdm

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines
from ..logs import setup_logging

logger = logging.getLogger(__name__)


@dataclass
class Graph:
    nodes: dict[str, int] = field(default_factory=dict)
    edges: dict[str, set[str]] = field(
        default_factory=partial(defaultdict, set)  # type: ignore
    )


# regexp patter to parse:
# 'Valve FT has flow rate=6; tunnels lead to valves DW, BV, JA, FB, TV'
pattern = re.compile(
    r"^Valve (?P<name>\w+) has flow rate\=(?P<flow_rate>\d+)\; "
    r"tunnels? leads? to valves? (?P<edges>\w+(, \w+)*)$"
)


def parse_graph(filename: Path) -> Graph:
    graph = Graph()
    for line in get_stripped_lines(filename):
        match = pattern.match(line)
        assert match is not None, repr(line)
        name = match.group("name")
        flow_rate = int(match.group("flow_rate"))
        graph.nodes[name] = flow_rate
        for edge in match.group("edges").split(", "):
            graph.edges[name].add(edge)
    return graph


def calculate_distances(graph: Graph) -> dict[str, dict[str, int]]:
    distances: dict[str, dict[str, int]] = {}

    all_nodes = set(graph.nodes)

    def _calculate_distances(node: str) -> dict[str, int]:
        visited: set[str] = set()
        costs: dict[str, int] = {node: 0}

        while len(visited) != len(all_nodes):
            lowest_unvisited_node = min(
                it.filterfalse(visited.__contains__, costs), key=costs.__getitem__
            )
            unvisited_neighbours = set(graph.edges[lowest_unvisited_node]) - visited
            for neighbour in unvisited_neighbours:
                costs[neighbour] = costs[lowest_unvisited_node] + 1
            visited.add(lowest_unvisited_node)

        return costs

    for node in tqdm.tqdm(all_nodes, desc="Calculating distances"):
        distances[node] = _calculate_distances(node)
    return distances


class PossibleValve(NamedTuple):
    node: str
    cost: int
    reward: int


def relu(x: int) -> int:
    return max(0, x)


def get_possible_moves(
    *,
    throughputs: dict[str, int],
    all_working_nodes: frozenset[str],
    opened: frozenset[str],
    distances_from_current: dict[str, int],
    remaining_time: int,
) -> Iterable[PossibleValve]:
    for node in all_working_nodes - opened:
        # cost is number of minutes of walking + one minute to open the valve
        cost = distances_from_current[node] + 1
        if cost >= remaining_time:
            # do not analyse valves that cannot be reached
            # or that are reached in the last minute
            continue
        # reward would be the throughput of the valve times the remaining time
        reward = throughputs[node] * relu(remaining_time - cost)
        yield PossibleValve(node, cost, reward)


def dfs(graph: Graph, *, time: int) -> int:
    distances = calculate_distances(graph)
    cache: dict[tuple[frozenset[str], str, int], int] = {}

    # it only makes sense to open valves that have a positive throughput
    all_working_nodes = frozenset(
        node for node, throughput in graph.nodes.items() if throughput > 0
    )

    def _dfs(*, opened: frozenset[str], current: str, remaining_time: int) -> int:
        key = (opened, current, remaining_time)
        if key in cache:
            return cache[key]
        # determine which valves are left to be opened
        possible_valves = get_possible_moves(
            throughputs=graph.nodes,
            all_working_nodes=all_working_nodes,
            opened=opened,
            distances_from_current=distances[current],
            remaining_time=remaining_time,
        )
        # order the possible values by potential reward
        # possible_valves.sort(key=lambda valve: valve.reward, reverse=True)
        total_rewards = (
            valve.reward
            + _dfs(
                opened=opened | {valve.node},
                current=valve.node,
                remaining_time=remaining_time - valve.cost,
            )
            for valve in possible_valves
        )
        best_reward = cache[key] = max(total_rewards, default=0)

        return best_reward

    return _dfs(opened=frozenset(), current="AA", remaining_time=time)


def visualize_graph(graph: Graph) -> None:
    import pydot

    g = pydot.Dot("my_graph", graph_type="digraph")
    for node in graph.nodes:
        g.add_node(pydot.Node(node, label=f"{node} ({graph.nodes[node]})"))
    for start_node, end_nodes in graph.edges.items():
        for end_node in end_nodes:
            g.add_edge(pydot.Edge(start_node, end_node))

    g.write_png("graph.png")


@wrap_main
def main(filename: Path) -> str:
    graph = parse_graph(filename)
    visualize_graph(graph)
    best_score = dfs(graph, time=30)
    return str(best_score)


if __name__ == "__main__":
    setup_logging()
    main()
