from functools import partial
from pathlib import Path
from typing import Callable

import numpy as np
from numpy import typing as npt

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines


def parse_matrix(filename: Path) -> npt.NDArray[np.uint8]:
    return np.array(
        list(
            map(
                lambda items: list(items),
                map(
                    partial(map, int),
                    map(lambda items: list(items), get_stripped_lines(filename)),
                ),
            )
        ),
        dtype=np.uint8,
    )


def map_matrix(
    matrix: npt.NDArray[np.uint8],
    callback: Callable[[list[npt.NDArray[np.uint8]], int], int],
) -> npt.NDArray[np.uint64]:
    height, width = matrix.shape
    result = np.zeros_like(matrix, dtype=np.uint64)
    for row_idx in range(height):
        for col_idx in range(width):
            current_height = matrix[row_idx, col_idx]
            # check if any tree to the north is shorter
            north = matrix[:row_idx, col_idx]
            south = matrix[row_idx + 1 :, col_idx]
            west = matrix[row_idx, :col_idx]
            east = matrix[row_idx, col_idx + 1 :]

            value = callback([north, south, west, east], current_height)
            result[row_idx, col_idx] = value
    return result


@wrap_main
def main(filename: Path) -> str:
    matrix = parse_matrix(filename)
    visible = map_matrix(
        matrix,
        lambda directions, current_height: any(
            (direction < current_height).all() for direction in directions
        ),
    )
    return str(visible.sum())


if __name__ == "__main__":
    main()
