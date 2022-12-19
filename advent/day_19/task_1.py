import itertools as it
import logging
import operator
import re
from copy import copy
from dataclasses import dataclass
from pathlib import Path
from typing import NewType

import tqdm
from returns.curry import partial

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


@dataclass(unsafe_hash=True)
class State:
    ore: Ore = Ore(0)
    clay: Clay = Clay(0)
    obsidian: Obsidian = Obsidian(0)
    geode: Geode = Geode(0)

    ore_robots: int = 1
    clay_robots: int = 0
    obsidian_robots: int = 0
    geode_robots: int = 0

    time_left: int = 24


def collect_resources(state: State) -> None:
    state.ore = Ore(state.ore + state.ore_robots)
    state.clay = Clay(state.clay + state.clay_robots)
    state.obsidian = Obsidian(state.obsidian + state.obsidian_robots)
    state.geode = Geode(state.geode + state.geode_robots)


@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0

    @property
    def total(self) -> int:
        return self.hits + self.misses


def _score_blueprint(
    cache: dict[State, State],
    blueprint: BluePrint,
    state: State,
) -> State:
    if state in cache:
        return cache[state]

    next_state = copy(state)

    # robots are harvesting resources
    collect_resources(next_state)

    # time is running out
    next_state.time_left -= 1

    if next_state.time_left == 0:
        cache[state] = next_state
        logger.debug("Reached possible end state with score %s", next_state.geode)
        return next_state

    # We have the following possibilities (exclusive):
    possibilities: list[State] = []
    # build a geode robot
    geode_cost_ore, geode_cost_obsidian = blueprint.geode_robot_cost
    if state.ore >= geode_cost_ore and state.obsidian >= geode_cost_obsidian:
        build_geode_robot_possibility = copy(next_state)
        build_geode_robot_possibility.ore = Ore(
            build_geode_robot_possibility.ore - geode_cost_ore
        )
        build_geode_robot_possibility.obsidian = Obsidian(
            build_geode_robot_possibility.obsidian - geode_cost_obsidian
        )
        build_geode_robot_possibility.geode_robots += 1
        # return _score_blueprint(cache, blueprint, build_geode_robot_possibility)
        possibilities.append(build_geode_robot_possibility)
    # build an obsidian robot
    obsidian_cost_ore, obsidian_cost_clay = blueprint.obsidian_robot_cost
    if state.ore >= obsidian_cost_ore and state.clay >= obsidian_cost_clay:
        build_obsidian_robot_possibility = copy(next_state)
        build_obsidian_robot_possibility.ore = Ore(
            build_obsidian_robot_possibility.ore - obsidian_cost_ore
        )
        build_obsidian_robot_possibility.clay = Clay(
            build_obsidian_robot_possibility.clay - obsidian_cost_clay
        )
        build_obsidian_robot_possibility.obsidian_robots += 1
        possibilities.append(build_obsidian_robot_possibility)
        # return _score_blueprint(cache, blueprint, build_obsidian_robot_possibility)
    # build a clay robot
    if state.clay >= blueprint.clay_robot_cost:
        build_clay_robot_possibility = copy(next_state)
        build_clay_robot_possibility.clay = Clay(
            build_clay_robot_possibility.clay - blueprint.clay_robot_cost
        )
        build_clay_robot_possibility.clay_robots += 1
        possibilities.append(build_clay_robot_possibility)
        # return _score_blueprint(cache, blueprint, build_clay_robot_possibility)
    # build an ore robot
    if state.ore >= blueprint.ore_robot_cost:
        build_ore_robot_possibility = copy(next_state)
        build_ore_robot_possibility.ore = Ore(
            build_ore_robot_possibility.ore - blueprint.ore_robot_cost
        )
        build_ore_robot_possibility.ore_robots += 1
        possibilities.append(build_ore_robot_possibility)
        # return _score_blueprint(cache, blueprint, build_ore_robot_possibility)

    # return _score_blueprint(cache, blueprint, next_state)
    # wait
    possibilities.append(next_state)

    best_state = cache[state] = max(
        map(partial(_score_blueprint, cache, blueprint), possibilities),
        key=lambda s: s.geode,
    )
    return best_state


def score_blueprint(blueprint: BluePrint) -> Geode:
    cache: dict[State, Geode] = {}
    state = State()
    state.clay = Clay(state.clay + blueprint.clay_robot_cost)
    state.time_left -= blueprint.clay_robot_cost

    best_state = _score_blueprint(cache, blueprint, state)
    best_score = best_state.geode
    logger.info("Blueprint scored %d with %s", best_score, best_state)
    return best_score


@wrap_main
def main(filename: Path) -> str:
    blueprints = parse_blueprints(filename)
    scores: dict[BluePrintId, Geode] = {
        blueprint_id: score_blueprint(blueprint)
        for blueprint_id, blueprint in tqdm.tqdm(blueprints.items(), desc="Blueprints")
    }
    levels = it.starmap(operator.mul, scores.items())
    total = sum(levels)
    return str(total)


if __name__ == "__main__":
    setup_logging(logging.INFO)
    main()
