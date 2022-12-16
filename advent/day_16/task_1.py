import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path

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


def dfs(graph: Graph, *, opened: set[str], current: str, remaining_time: int) -> int:
    cache: dict[tuple[frozenset[str], str, int], int] = {}

    def _dfs(*, opened: frozenset[str], current: str, remaining_time: int) -> int:
        if remaining_time == 0:
            return 0
        key = (opened, current, remaining_time)
        if key in cache:
            return cache[key]
        # at each step we taka a decision: either we open a new value or we move
        possible_scores: list[int] = [0]
        can_open_current_value = current not in opened and graph.nodes[current] > 0
        if can_open_current_value:
            current_throughput = graph.nodes[current]
            open_score = (
                _dfs(
                    opened=opened | {current},
                    current=current,
                    remaining_time=remaining_time - 1,
                )
                + (remaining_time - 1) * current_throughput
            )
            possible_scores.append(open_score)
        possible_destinations = graph.edges[current]
        for destination in possible_destinations:
            move_score = _dfs(
                opened=opened,
                current=destination,
                remaining_time=remaining_time - 1,
            )
            possible_scores.append(move_score)
        best_score = cache[key] = max(possible_scores)
        return best_score

    return _dfs(
        opened=frozenset(opened), current=current, remaining_time=remaining_time
    )


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
    best_score = dfs(graph, opened=set(), current="AA", remaining_time=30)
    return str(best_score)


if __name__ == "__main__":
    setup_logging()
    main()
