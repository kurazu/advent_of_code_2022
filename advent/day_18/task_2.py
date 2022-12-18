import logging
from collections import deque
from pathlib import Path

import more_itertools as mit

from ..cli_utils import wrap_main
from ..logs import setup_logging
from .task_1 import DS, add_, read_voxels

logger = logging.getLogger(__name__)


@wrap_main
def main(filename: Path) -> str:
    voxels = set(read_voxels(filename))

    min_x, max_x = mit.minmax(x for x, _, _ in voxels)
    min_y, max_y = mit.minmax(y for _, y, _ in voxels)
    min_z, max_z = mit.minmax(z for _, _, z in voxels)

    logger.debug("x: %d - %d (span %d)", min_x, max_x, max_x - min_x)
    logger.debug("y: %d - %d (span %d)", min_y, max_y, max_y - min_y)
    logger.debug("z: %d - %d (span %d)", min_z, max_z, max_z - min_z)

    origin = (min_x, min_y, min_z)
    assert origin not in voxels  # make sure that the origin is empty

    def is_in_span(voxel: tuple[int, int, int]) -> bool:
        x, y, z = voxel
        return (
            (min_x - 1) <= x <= (max_x + 1)
            and (min_y - 1) <= y <= (max_y + 1)
            and (min_z - 1) <= z <= (max_z + 1)
        )

    visited: set[tuple[int, int, int]] = set()
    to_visit: deque[tuple[int, int, int]] = deque()
    to_visit.append(origin)

    surface = 0
    while to_visit:
        voxel = to_visit.popleft()
        if voxel in visited:
            continue
        neighbouring_voxels = map(lambda d: add_(voxel, d), DS)
        neighbouring_voxels_in_span = filter(is_in_span, neighbouring_voxels)
        unvisited_neighbouring_voxels = filter(
            lambda nv: nv not in visited, neighbouring_voxels_in_span
        )
        for nv in unvisited_neighbouring_voxels:
            if nv in voxels:  # found a touch point with lava
                surface += 1
            else:  # new empty voxel to visit
                to_visit.append(nv)
        visited.add(voxel)

    return str(surface)


if __name__ == "__main__":
    setup_logging()
    main()
