from __future__ import annotations

import io
import itertools as it
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, TypeVar

import more_itertools as mit

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines
from ..logs import setup_logging

logger = logging.getLogger(__name__)


T = TypeVar("T")


def assert_not_none(value: T | None) -> T:
    assert value is not None
    return value


@dataclass
class Node:
    value: int = field(kw_only=True)
    next: Node | None = field(default=None, init=False, repr=False)
    prev: Node | None = field(default=None, init=False, repr=False)

    def __repr__(self) -> str:
        buf = io.StringIO()
        buf.write("[")
        first = True
        node = self
        while True:
            if first:
                first = False
            else:
                buf.write(", ")
            buf.write(str(node.value))
            node = assert_not_none(node.next)
            if node is self:
                break
        buf.write("]")
        return buf.getvalue()


def cut_node(node: Node) -> tuple[Node, Node]:
    """
    Disconnects the node from the double linked list
    and returns the previous and next nodes.
    """
    prev_node = assert_not_none(node.prev)
    next_node = assert_not_none(node.next)
    prev_node.next = next_node
    next_node.prev = prev_node
    node.prev = None
    node.next = None
    return prev_node, next_node


def insert_in_between(prev_node: Node, next_node: Node, node: Node) -> None:
    """Insert node between two given nodes."""
    assert node.prev is None
    assert node.next is None
    assert prev_node.next is next_node
    assert next_node.prev is prev_node

    prev_node.next = node
    node.prev = prev_node

    next_node.prev = node
    node.next = next_node


def move_right(node: Node, steps: int) -> None:
    """Move the node right by the given number of steps."""
    assert steps > 0
    prev_node, next_node = cut_node(node)

    for _ in range(steps):
        prev_node = next_node
        next_node = assert_not_none(next_node.next)

    insert_in_between(prev_node=prev_node, next_node=next_node, node=node)


def move_left(node: Node, steps: int) -> None:
    """Move the node left by the given number of steps."""
    assert steps > 0
    prev_node, next_node = cut_node(node)

    for _ in range(steps):
        next_node = prev_node
        prev_node = assert_not_none(prev_node.prev)

    insert_in_between(prev_node=prev_node, next_node=next_node, node=node)


def read_numbers(filename: Path) -> Iterable[int]:
    return map(int, get_stripped_lines(filename))


def mix(nodes_in_order: list[Node]) -> None:
    for node in nodes_in_order:
        logger.debug("Before mixing %r", node)
        offset = node.value
        if offset == 0:
            continue
        elif offset > 0:
            move_right(node, offset)
        else:
            move_left(node, -offset)
        logger.debug("After mixing %r", node)


def to_linked_list(numbers: Iterable[int]) -> list[Node]:
    nodes: list[Node] = []
    prev_node: Node | None = None
    for value in numbers:
        node = Node(value=value)
        if prev_node is not None:
            prev_node.next = node
        node.prev = prev_node
        prev_node = node
        nodes.append(node)
    assert prev_node is not None
    first_node = nodes[0]
    first_node.prev = prev_node
    prev_node.next = first_node
    return nodes


def find_value(node: Node, value: int) -> Node:
    while node.value != value:
        node = assert_not_none(node.next)
    return node


def fast_forward(node: Node, steps: int) -> Node:
    for _ in range(steps):
        node = assert_not_none(node.next)
    return node


@wrap_main
def main(filename: Path) -> str:
    numbers = read_numbers(filename)
    nodes_in_order = to_linked_list(numbers)
    mix(nodes_in_order)

    zero_node = find_value(nodes_in_order[0], 0)
    logger.debug("Zero node: %r", zero_node)

    node1000 = fast_forward(zero_node, 1000)
    logger.debug("Node after 1000 steps: %d", node1000.value)
    node2000 = fast_forward(node1000, 1000)
    logger.debug("Node after 2000 steps: %d", node2000.value)
    node3000 = fast_forward(node2000, 1000)
    logger.debug("Node after 3000 steps: %d", node3000.value)
    total = node1000.value + node2000.value + node3000.value
    return str(total)


if __name__ == "__main__":
    setup_logging(logging.INFO)
    main()
