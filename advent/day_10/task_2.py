import io
import itertools as it
import logging
from pathlib import Path
from typing import Iterable

from ..cli_utils import wrap_main
from ..logs import setup_logging
from .task_1 import Interpreter, load_program

logger = logging.getLogger(__name__)


def get_pixels(states: Iterable[int]) -> Iterable[bool]:
    for idx, state in enumerate(states):
        pixel = idx % 40
        yield abs(pixel - state) <= 1


def visualize_pixels(pixels: Iterable[bool]) -> str:
    buf = io.StringIO()
    extra_chars = it.cycle(it.chain(it.repeat("", 39), "\n"))
    for pixel, extra_char in zip(pixels, extra_chars):
        buf.write("#" if pixel else " ")
        buf.write(extra_char)
    return buf.getvalue()


@wrap_main
def main(filename: Path) -> str:
    program = load_program(filename)
    interpreter = Interpreter(program)
    states = interpreter.run(240)
    pixels = get_pixels(states)
    return visualize_pixels(pixels)


if __name__ == "__main__":
    setup_logging()
    main()
