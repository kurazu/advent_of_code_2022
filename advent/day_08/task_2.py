import operator
from functools import reduce
from pathlib import Path

import numpy as np
from numpy import typing as npt

from ..cli_utils import wrap_main
from .task_1 import map_matrix, parse_matrix


def get_score(directions: list[npt.NDArray[np.uint8]], current_height: int) -> int:
    def _get_score(direction: npt.NDArray[np.uint8]) -> int:
        i = 0
        for i, tree in enumerate(direction, 1):
            if tree >= current_height:
                break
        return i

    scores = map(_get_score, directions)
    return reduce(operator.mul, scores)


@wrap_main
def main(filename: Path) -> str:
    matrix = parse_matrix(filename)
    scores = map_matrix(matrix, get_score)
    return str(scores.max())


if __name__ == "__main__":
    main()
