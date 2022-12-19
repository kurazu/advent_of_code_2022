import logging
import multiprocessing as mp
import re
from copy import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, NewType

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
    id: BluePrintId
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


def parse_blueprints(filename: Path) -> Iterable[BluePrint]:
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
        yield BluePrint(
            id=blueprint_id,
            ore_robot_cost=ore_robot_cost,
            clay_robot_cost=clay_robot_cost,
            obsidian_robot_cost=obsidian_robot_cost,
            geode_robot_cost=geode_robot_cost,
        )


@dataclass(unsafe_hash=True)
class State:
    time_left: int

    ore: Ore = Ore(0)
    clay: Clay = Clay(0)
    obsidian: Obsidian = Obsidian(0)
    geode: Geode = Geode(0)

    ore_robots: int = 1
    clay_robots: int = 0
    obsidian_robots: int = 0
    geode_robots: int = 0

    def score(self) -> Geode:
        return self.geode


def collect_resources(state: State) -> None:
    state.ore = Ore(state.ore + state.ore_robots)
    state.clay = Clay(state.clay + state.clay_robots)
    state.obsidian = Obsidian(state.obsidian + state.obsidian_robots)
    state.geode = Geode(state.geode + state.geode_robots)


def get_wait_state(state: State) -> State:
    next_state = copy(state)

    # robots are harvesting resources
    collect_resources(next_state)

    # time is running out
    next_state.time_left -= 1

    return next_state


def get_possible_next_states(
    blueprint: BluePrint, *, state: State, wait_state: State
) -> Iterable[State]:
    # We have the following possibilities (exclusive):
    # build a geode robot
    geode_cost_ore, geode_cost_obsidian = blueprint.geode_robot_cost
    if state.ore >= geode_cost_ore and state.obsidian >= geode_cost_obsidian:
        build_geode_robot_possibility = copy(wait_state)
        build_geode_robot_possibility.ore = Ore(
            build_geode_robot_possibility.ore - geode_cost_ore
        )
        build_geode_robot_possibility.obsidian = Obsidian(
            build_geode_robot_possibility.obsidian - geode_cost_obsidian
        )
        build_geode_robot_possibility.geode_robots += 1
        yield build_geode_robot_possibility
        # if we can build a geode robot, we don't need to consider
        # any other possibilities, because adding a geode robot adds geode resource
        # and directly increases the score
        return

    # build an obsidian robot
    obsidian_cost_ore, obsidian_cost_clay = blueprint.obsidian_robot_cost
    if state.ore >= obsidian_cost_ore and state.clay >= obsidian_cost_clay:
        build_obsidian_robot_possibility = copy(wait_state)
        build_obsidian_robot_possibility.ore = Ore(
            build_obsidian_robot_possibility.ore - obsidian_cost_ore
        )
        build_obsidian_robot_possibility.clay = Clay(
            build_obsidian_robot_possibility.clay - obsidian_cost_clay
        )
        build_obsidian_robot_possibility.obsidian_robots += 1
        yield build_obsidian_robot_possibility

    # build a clay robot
    if state.ore >= blueprint.clay_robot_cost:
        build_clay_robot_possibility = copy(wait_state)
        build_clay_robot_possibility.ore = Ore(
            build_clay_robot_possibility.ore - blueprint.clay_robot_cost
        )
        build_clay_robot_possibility.clay_robots += 1
        yield build_clay_robot_possibility

    # build an ore robot
    if state.ore >= blueprint.ore_robot_cost:
        build_ore_robot_possibility = copy(wait_state)
        build_ore_robot_possibility.ore = Ore(
            build_ore_robot_possibility.ore - blueprint.ore_robot_cost
        )
        build_ore_robot_possibility.ore_robots += 1
        yield build_ore_robot_possibility

    # wait and construct no robots
    yield wait_state


def _score_blueprint(
    cache: dict[State, State],
    blueprint: BluePrint,
    depth: int,
    state: State,
) -> State:
    if state in cache:
        return cache[state]

    wait_state = get_wait_state(state)

    if wait_state.time_left == 0:
        # This is the final state - no point in constructing any more robots
        cache[state] = wait_state
        logger.debug("Reached possible end state with score %s", wait_state.geode)
        return wait_state

    possibilities = get_possible_next_states(
        blueprint, state=state, wait_state=wait_state
    )

    # if depth < 12:
    #     possibilities = list(possibilities)
    #     possibilities = tqdm.tqdm(possibilities, desc=f"Depth {depth}")

    best_state = cache[state] = max(
        map(
            partial(_score_blueprint, cache, blueprint, depth + 1),
            possibilities,
        ),
        key=State.score,
    )
    return best_state


def score_blueprint(blueprint: BluePrint, time_left: int) -> int:
    cache: dict[State, State] = {}
    state = State(time_left=time_left)

    best_state = _score_blueprint(cache, blueprint, 0, state)
    best_score = best_state.score()
    logger.info(
        "Blueprint %d scored %d with states %s", blueprint.id, best_score, best_state
    )

    # logger.info("Starting explanation")
    # logger.info("Initial state: %s", state)
    # breakpoint()
    # # start explanations
    # while state.time_left > 0:
    #     logger.info("State: %s", state)
    #     wait_state = get_wait_state(state)
    #     possibilities = get_possible_next_states(
    #         blueprint, state=state, wait_state=wait_state
    #     )
    #     best_possibility = max(
    #         possibilities, key=lambda possibility: cache[possibility].score()
    #     )
    #     logger.info(
    #         "From state %s we select best possibility %s", state, best_possibility
    #     )
    #     state = best_possibility

    # breakpoint()
    return best_score


def score_and_multiply(blueprint: BluePrint) -> int:
    best_score = score_blueprint(blueprint, time_left=24)
    return best_score * blueprint.id


@wrap_main
def main(filename: Path) -> str:
    blueprints = list(parse_blueprints(filename))
    with mp.Pool(4) as pool:
        scores = tqdm.tqdm(
            pool.imap(score_and_multiply, blueprints, chunksize=1),
            total=len(blueprints),
        )
        total = sum(scores)
    return str(total)


if __name__ == "__main__":
    setup_logging(logging.WARNING)
    main()
