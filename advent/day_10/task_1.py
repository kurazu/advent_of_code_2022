import itertools as it
import logging
import operator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Protocol

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines
from ..logs import setup_logging

logger = logging.getLogger(__name__)


@dataclass
class InterpreterState:
    x: int = 1


class Instruction(Protocol):
    def __call__(self, state: InterpreterState) -> Iterable[None]:
        ...


class Noop:
    def __call__(self, state: InterpreterState) -> Iterable[None]:
        yield


@dataclass
class AddX:
    increment: int

    def __call__(self, state: InterpreterState) -> Iterable[None]:
        yield
        yield
        state.x += self.increment


def parse_instruction(line: str) -> Instruction:
    if line == "noop":
        return Noop()
    elif line.startswith("addx"):
        name, value_str = line.split(" ")
        return AddX(increment=int(value_str))
    else:
        raise ValueError(f"Unknown instruction {line}")


def load_program(filename: Path) -> list[Instruction]:
    return [parse_instruction(line) for line in get_stripped_lines(filename)]


class Interpreter:
    current_instruction: Instruction
    current_op: Iterable[None]

    def __init__(self, program: list[Instruction]) -> None:
        self.state = InterpreterState()
        logger.debug("Intializing interpreter with state %s", self.state)
        self.instructions = it.cycle(program)
        self.shift_instruction()

    def shift_instruction(self) -> None:
        self.current_instruction = next(self.instructions)
        self.current_op = self.current_instruction(self.state)
        logger.info("Shifted to instruction %s", self.current_instruction)

    def step(self) -> int:
        logger.debug(
            "Stepping with state %s @ %s", self.state, self.current_instruction
        )
        try:
            next(self.current_op)
        except StopIteration:
            logger.debug("Instruction %s finished", self.current_instruction)
            self.shift_instruction()
            next(self.current_op)
        else:
            logger.debug(
                "Stepped with state %s @ %s", self.state, self.current_instruction
            )

    def run(self, cycles: int) -> Iterable[tuple[int, int]]:
        for cycle in range(1, cycles + 1):
            self.step()
            yield cycle, self.state.x


@wrap_main
def main(filename: Path) -> str:
    program = load_program(filename)
    interpreter = Interpreter(program)
    cycle_state = interpreter.run(220)
    interesting: Iterable[tuple[int, int]] = it.islice(cycle_state, 19, None, 40)
    interesting = list(interesting)
    logger.info("Interesting states: %s", interesting)
    signal_strengths = it.starmap(operator.mul, interesting)
    total = sum(signal_strengths)
    return str(total)


if __name__ == "__main__":
    setup_logging()
    main()
