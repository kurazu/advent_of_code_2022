import itertools as it
import logging
from pathlib import Path
from typing import Iterable

import more_itertools as mit
import numpy as np
from numpy import typing as npt

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines
from ..logs import setup_logging

logger = logging.getLogger(__name__)


def read_numbers(filename: Path) -> Iterable[int]:
    return map(int, get_stripped_lines(filename))


def mix(
    numbers: npt.NDArray[np.int32], indices: npt.NDArray[np.uint32]
) -> npt.NDArray[np.int32]:
    return numbers


@wrap_main
def main(filename: Path) -> str:
    numbers = np.array(list(read_numbers(filename)), dtype=np.int32)
    indices = np.arange(len(numbers), dtype=np.uint32)
    logger.debug("Read %d numbers", len(numbers))
    mixed = mix(numbers, indices)
    zero_index: int
    ((zero_index,),) = np.where(mixed == 0)
    wrapped = it.cycle(it.chain(mixed[zero_index:], mixed[:zero_index]))
    items = (mit.nth(wrapped, 1000) for _ in range(3))
    for item in items:
        logger.debug("Item: %d", item)
    return ""


if __name__ == "__main__":
    setup_logging()
    main()
