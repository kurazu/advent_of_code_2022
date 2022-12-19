import functools
import logging
import math
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


@dataclass
class GlobalState:
    best_score: Geode = Geode(-1)


def state_after_waiting(state: State, turns_to_wait: int) -> State:
    next_state = copy(state)
    next_state.time_left -= turns_to_wait
    next_state.ore = Ore(next_state.ore + next_state.ore_robots * turns_to_wait)
    next_state.clay = Clay(next_state.clay + next_state.clay_robots * turns_to_wait)
    next_state.obsidian = Obsidian(
        next_state.obsidian + next_state.obsidian_robots * turns_to_wait
    )
    next_state.geode = Geode(next_state.geode + next_state.geode_robots * turns_to_wait)
    return next_state


def relu(x: int) -> int:
    return max(0, x)


def _get_ore_robot_possibility(blueprint: BluePrint, state: State) -> Iterable[State]:
    missing_ore = blueprint.ore_robot_cost - state.ore
    turns_to_wait = math.ceil(relu(missing_ore) / state.ore_robots) + 1
    if turns_to_wait >= state.time_left:
        # no point in making this robot, we won't have enought time to use it
        return

    ore_robot_possibility = state_after_waiting(state, turns_to_wait)
    ore_robot_possibility.ore_robots += 1
    ore_robot_possibility.ore = Ore(
        ore_robot_possibility.ore - blueprint.ore_robot_cost
    )
    yield ore_robot_possibility


def _get_clay_robot_possibility(blueprint: BluePrint, state: State) -> Iterable[State]:
    missing_ore = relu(blueprint.clay_robot_cost - state.ore)
    turns_to_wait = math.ceil(missing_ore / state.ore_robots) + 1
    if turns_to_wait >= state.time_left:
        # no point in making this robot, we won't have enought time to use it
        return

    clay_robot_possibility = state_after_waiting(state, turns_to_wait)
    clay_robot_possibility.clay_robots += 1
    clay_robot_possibility.ore = Ore(
        clay_robot_possibility.ore - blueprint.clay_robot_cost
    )
    yield clay_robot_possibility


def _get_obsidian_robot_possibility(
    blueprint: BluePrint, state: State
) -> Iterable[State]:
    if not state.clay_robots:
        return  # we cannot make obsidian robots without clay robots

    robot_cost_ore, robot_cost_clay = blueprint.obsidian_robot_cost

    missing_ore = relu(robot_cost_ore - state.ore)
    turns_to_wait_for_ore = math.ceil(missing_ore / state.ore_robots)

    missing_clay = relu(robot_cost_clay - state.clay)
    turns_to_wait_for_clay = math.ceil(missing_clay / state.clay_robots)

    turns_to_wait = max(turns_to_wait_for_ore, turns_to_wait_for_clay) + 1
    if turns_to_wait >= state.time_left:
        # no point in making this robot, we won't have enought time to use it
        return

    obsidian_robot_possibility = state_after_waiting(state, turns_to_wait)
    obsidian_robot_possibility.obsidian_robots += 1
    obsidian_robot_possibility.ore = Ore(
        obsidian_robot_possibility.ore - robot_cost_ore
    )
    obsidian_robot_possibility.clay = Clay(
        obsidian_robot_possibility.clay - robot_cost_clay
    )
    yield obsidian_robot_possibility


def _get_geode_robot_possibility(blueprint: BluePrint, state: State) -> Iterable[State]:
    if not state.obsidian_robots:
        return  # we cannot make geode robots without obsidian robots

    robot_cost_ore, robot_cost_obsidian = blueprint.geode_robot_cost

    missing_ore = relu(robot_cost_ore - state.ore)
    turns_to_wait_for_ore = math.ceil(missing_ore / state.ore_robots)

    missing_obsidian = relu(robot_cost_obsidian - state.obsidian)
    turns_to_wait_for_obsidian = math.ceil(missing_obsidian / state.obsidian_robots)

    turns_to_wait = max(turns_to_wait_for_ore, turns_to_wait_for_obsidian) + 1
    if turns_to_wait >= state.time_left:
        # no point in making this robot, we won't have enought time to use it
        return

    geode_robot_possibility = state_after_waiting(state, turns_to_wait)
    geode_robot_possibility.geode_robots += 1
    geode_robot_possibility.ore = Ore(geode_robot_possibility.ore - robot_cost_ore)
    geode_robot_possibility.obsidian = Obsidian(
        geode_robot_possibility.obsidian - robot_cost_obsidian
    )
    yield geode_robot_possibility


def _get_possible_next_states(blueprint: BluePrint, *, state: State) -> Iterable[State]:
    # We are choosing between 4 actions:
    # 1. accumulate resources and build a geode robot
    # 2. accumulate resources and build an obsidian robot
    # 3. accumulate resources and build a clay robot
    # 4. accumulate resources and build an ore robot
    # Because of the accumulation of resources, different actions can push the time
    # to different points in the future.

    yield from _get_geode_robot_possibility(blueprint, state)
    yield from _get_obsidian_robot_possibility(blueprint, state)
    yield from _get_clay_robot_possibility(blueprint, state)
    yield from _get_ore_robot_possibility(blueprint, state)


@functools.cache
def _get_max_score(geode: Geode, geode_robots: int, time_left: int) -> Geode:
    score = geode
    for _ in range(time_left):
        # for the best possible scenario, assume that there will be a new geode robot
        # constructed each turn
        score = Geode(score + geode_robots)
        geode_robots += 1
    return score


def get_max_score(state: State) -> Geode:
    return _get_max_score(state.geode, state.geode_robots, state.time_left)


def _score_blueprint(
    cache: dict[State, State],
    global_state: GlobalState,
    blueprint: BluePrint,
    state: State,
) -> State:
    if state in cache:
        return cache[state]

    possibilities = _get_possible_next_states(blueprint, state=state)
    possibilities = filter(
        lambda p: get_max_score(p) > global_state.best_score, possibilities
    )

    possibilities = list(possibilities)
    if not possibilities:
        # if we cannot construct any more robots, the only things we can do is wait
        wait_state = cache[state] = state_after_waiting(state, state.time_left)
        if wait_state.geode > global_state.best_score:
            global_state.best_score = wait_state.geode
        return wait_state

    best_state = cache[state] = max(
        map(
            partial(_score_blueprint, cache, global_state, blueprint),
            possibilities,
        ),
        key=State.score,
    )
    return best_state


def score_blueprint(blueprint: BluePrint, time_left: int) -> int:
    cache: dict[State, State] = {}
    global_state = GlobalState()
    state = State(time_left=time_left)

    best_state = _score_blueprint(cache, global_state, blueprint, state)
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
