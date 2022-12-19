import itertools as it
import logging
import operator
import re
from dataclasses import dataclass
from pathlib import Path
from typing import NewType

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines
from ..logs import setup_logging

logger = logging.getLogger(__name__)


BluePrintId = NewType("BluePrintId", int)
Ore = NewType("Ore", int)
Clay = NewType("Clay", int)
Obsidian = NewType("Obsidian", int)
Geode = NewType("Geode", int)


@dataclass
class BluePrint:
    ore_robot_cost: Ore
    clay_robot_cost: Ore
    obsidian_robot_cost: tuple[Ore, Clay]
    geode_robot_cost: tuple[Ore, Obsidian]


pattern = re.compile(
    r"^Blueprint (?P<blueprint_id>\d+)\: "
    r"Each ore robot costs (?P<ore_robot_cost_ore>\d+) ore\. "
    r"Each clay robot costs (?P<clay_robot_cost_ore>\d+) ore\. "
    r"Each obsidian robot costs (?P<obsidian_robot_cost_ore>\d+) ore "
    r"and (?P<obsidian_robot_cost_clay>\d+) clay\. "
    r"Each geode robot costs (?P<geode_robot_cost_ore>\d+) ore "
    r"and (?P<geode_robot_cost_obsidian>\d+) obsidian\.$"
)


def parse_blueprints(filename: Path) -> dict[BluePrintId, BluePrint]:
    blueprints: dict[BluePrintId, BluePrint] = {}
    for line in get_stripped_lines(filename):
        match = pattern.match(line)
        assert match is not None
        blueprint_id = BluePrintId(int(match.group("blueprint_id")))
        ore_robot_cost = Ore(int(match.group("ore_robot_cost_ore")))
        clay_robot_cost = Ore(int(match.group("clay_robot_cost_ore")))
        obsidian_robot_cost = (
            Ore(int(match.group("obsidian_robot_cost_ore"))),
            Clay(int(match.group("obsidian_robot_cost_clay"))),
        )
        geode_robot_cost = (
            Ore(int(match.group("geode_robot_cost_ore"))),
            Obsidian(int(match.group("geode_robot_cost_obsidian"))),
        )
        blueprints[blueprint_id] = BluePrint(
            ore_robot_cost=ore_robot_cost,
            clay_robot_cost=clay_robot_cost,
            obsidian_robot_cost=obsidian_robot_cost,
            geode_robot_cost=geode_robot_cost,
        )
    return blueprints


def score_blueprint(blueprint: BluePrint) -> Geode:
    return Geode(0)


@wrap_main
def main(filename: Path) -> str:
    blueprints = parse_blueprints(filename)
    scores: dict[BluePrintId, Geode] = {
        blueprint_id: score_blueprint(blueprint)
        for blueprint_id, blueprint in blueprints.items()
    }
    levels = it.starmap(operator.mul, scores.items())
    total = sum(levels)
    return str(total)


if __name__ == "__main__":
    setup_logging()
    main()
