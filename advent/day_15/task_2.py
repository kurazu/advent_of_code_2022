import bisect
import logging
import multiprocessing as mp
import re
from functools import partial
from pathlib import Path
from typing import Iterable, NamedTuple

import click
import matplotlib.pyplot as plt
import more_itertools as mit
import numpy as np
import tqdm
from matplotlib.patches import Ellipse, Rectangle
from numpy import typing as npt

from ..logs import setup_logging
from .task_1 import (
    Position,
    Sensor,
    can_have_beacon,
    get_highest_distance_between_sensor_and_beacon,
    manhattan_distance,
    parse_sensors,
)

logger = logging.getLogger(__name__)


def relu(x: int) -> int:
    return max(0, x)


def get_closest_sensor_by_x(sensors_by_x: list[Sensor], x: int) -> Sensor:
    left_i = max(0, bisect.bisect_left(sensors_by_x, x, key=Sensor.get_sensor_x))
    right_i = min(
        len(sensors_by_x) - 1,
        bisect.bisect_right(sensors_by_x, x, key=Sensor.get_sensor_x),
    )
    indices = {left_i, right_i}
    sensors = map(sensors_by_x.__getitem__, indices)
    return min(sensors, key=lambda s: abs(s.position.x - x))


def get_closest_sensor_by_y(sensors_by_y: list[Sensor], y: int) -> Sensor:
    left_i = max(0, bisect.bisect_left(sensors_by_y, y, key=Sensor.get_sensor_y))
    right_i = min(
        len(sensors_by_y) - 1,
        bisect.bisect_right(sensors_by_y, y, key=Sensor.get_sensor_y),
    )
    indices = {left_i, right_i}
    sensors = map(sensors_by_y.__getitem__, indices)
    return min(sensors, key=lambda s: abs(s.position.y - y))


def visualize_sensors(
    sensors: Iterable[Sensor], range_max_x: int, range_max_y: int
) -> None:

    fig, ax = plt.subplots(subplot_kw={"aspect": "equal"})
    for sensor in sensors:
        ellipse = Ellipse(
            xy=(sensor.position.x, sensor.position.y),
            width=sensor.r * 2,
            height=sensor.r * 2,
        )
        ax.add_artist(ellipse)
        # ellipse.set_clip_box(ax.bbox)
        ellipse.set_alpha(0.5)

    # automatically set ranges on x and y axes

    min_x, max_x = mit.minmax(map(lambda p: p.x, map(lambda s: s.position, sensors)))
    min_y, max_y = mit.minmax(map(lambda p: p.y, map(lambda s: s.position, sensors)))
    highest_distance_between_sensor_and_beacon = max(map(lambda s: s.r, sensors))
    min_x -= highest_distance_between_sensor_and_beacon
    max_x += highest_distance_between_sensor_and_beacon
    min_y -= highest_distance_between_sensor_and_beacon
    max_y += highest_distance_between_sensor_and_beacon

    ax.set_xlim(min_x, max_x)
    ax.set_ylim(min_y, max_y)

    # draw rectange from 0,0 to max_x,max_y
    rect = Rectangle(
        xy=(0, 0),
        width=range_max_x,
        height=range_max_y,
        fill=False,
        # set edge color to red
        edgecolor="red",
    )
    ax.add_artist(rect)

    # draw a dot at x=14, y=11
    ax.plot(14, 11, "ro", markersize=1)


def find_points(
    sensors_x: npt.NDArray[np.int32],
    sensors_y: npt.NDArray[np.int32],
    sensors_r: npt.NDArray[np.int32],
    max_x: int,
    y: int,
    batch_size: int = 5000,
) -> Position | None:
    y_dist = np.abs(sensors_y - y)[:, np.newaxis]
    for start_x in range(0, max_x + 1, batch_size):
        x = np.arange(start_x, min(max_x, start_x + batch_size), dtype=np.int32)
        x_dist = np.abs(np.subtract(sensors_x[:, np.newaxis], x))
        dist = x_dist + y_dist
        in_radius = np.any(dist <= sensors_r, axis=0)
        if np.all(in_radius):
            continue
        idx = np.argmin(in_radius)
        match_x = x[idx]
        return Position(y=y, x=match_x)
    return None


@click.command()
@click.argument(
    "filename",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        path_type=Path,
    ),
    required=True,
)
@click.argument("max_x", type=int, required=True)
@click.argument("max_y", type=int, required=True)
def main(filename: Path, max_x: int, max_y: int) -> None:
    sensors = list(parse_sensors(filename))

    highest_distance_between_sensor_and_beacon = (
        get_highest_distance_between_sensor_and_beacon(sensors)
    )
    logger.debug(
        "Highest distance between sensor and beacon: %d",
        highest_distance_between_sensor_and_beacon,
    )
    visualize_sensors(sensors, max_x, max_y)
    plt.savefig("sensors.png")

    sensors_x = np.array([s.position.x for s in sensors], np.int32)
    sensors_y = np.array([s.position.y for s in sensors], np.int32)
    sensors_r = np.array([s.r for s in sensors], np.int32)[:, np.newaxis]

    beacon_positions = {sensor.beacon for sensor in sensors}

    with mp.Pool(4) as pool:
        points_matching: Iterable[Position] = filter(
            None,
            tqdm.tqdm(
                pool.imap_unordered(
                    partial(
                        find_points,
                        sensors_x,
                        sensors_y,
                        sensors_r,
                        max_x,
                    ),
                    range(max_y + 1),
                ),
                total=max_y + 1,
            ),
        )
        for point in points_matching:
            logger.debug("Point %s can have a beacon", point)
            click.echo(str(point.x * 4000000 + point.y))
            return


if __name__ == "__main__":
    setup_logging()
    main()
