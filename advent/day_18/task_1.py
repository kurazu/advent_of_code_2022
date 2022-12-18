import logging
from pathlib import Path
from typing import Iterable, cast

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines
from ..logs import setup_logging

logger = logging.getLogger(__name__)


def read_voxels(filename: Path) -> Iterable[tuple[int, int, int]]:
    for line in get_stripped_lines(filename):
        parts = line.split(",")
        coords = map(int, parts)
        voxel = tuple(coords)
        yield cast(tuple[int, int, int], voxel)


def add_(
    voxel: tuple[int, int, int], delta: tuple[int, int, int]
) -> tuple[int, int, int]:
    return cast(tuple[int, int, int], tuple(x + dx for x, dx in zip(voxel, delta)))


DS: list[tuple[int, int, int]] = [
    (1, 0, 0),
    (0, 1, 0),
    (0, 0, 1),
    (-1, 0, 0),
    (0, -1, 0),
    (0, 0, -1),
]


@wrap_main
def main(filename: Path) -> str:
    voxels = set(read_voxels(filename))

    surface = 0
    for voxel in voxels:
        neighbouring_voxels = map(lambda d: add_(voxel, d), DS)
        surface += sum(1 for nv in neighbouring_voxels if nv not in voxels)
    return str(surface)


if __name__ == "__main__":
    setup_logging()
    main()
