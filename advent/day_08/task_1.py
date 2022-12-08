from functools import partial
from pathlib import Path
from typing import Callable, Iterable, TypeVar

import numpy as np

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines


@wrap_main
def main(filename: Path) -> str:
    matrix = np.array(
        list(
            map(
                list,
                map(partial(map, int), map(list, get_stripped_lines(filename))),
            )
        ),
        dtype=np.uint8,
    )
    height, width = matrix.shape
    visible_trees = 0
    visible = np.zeros_like(matrix, dtype=bool)
    for row_idx in range(height):
        for col_idx in range(width):
            current_height = matrix[row_idx, col_idx]
            # check if any tree to the north is shorter
            north = matrix[:row_idx, col_idx]
            south = matrix[row_idx + 1 :, col_idx]
            west = matrix[row_idx, :col_idx]
            east = matrix[row_idx, col_idx + 1 :]

            is_visible = (
                (north < current_height).all()
                or (south < current_height).all()
                or (west < current_height).all()
                or (east < current_height).all()
            )
            visible_trees += is_visible

    return str(visible_trees)


if __name__ == "__main__":
    main()
