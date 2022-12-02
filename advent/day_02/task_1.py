from __future__ import annotations

from enum import Enum
from pathlib import Path

import click


class Shape(str, Enum):
    ROCK = "X"
    PAPER = "Y"
    SCISSORS = "Z"


OPPONENT_SHAPE_TO_SHAPE: dict[str, Shape] = {
    "A": Shape.ROCK,
    "B": Shape.PAPER,
    "C": Shape.SCISSORS,
}


SHAPE_SCORES: dict[Shape, int] = {
    Shape.ROCK: 1,
    Shape.PAPER: 2,
    Shape.SCISSORS: 3,
}


class Result(int, Enum):
    WIN = 6
    DRAW = 3
    LOSS = 0


RESULTS: dict[tuple[Shape, Shape], Result] = {
    (Shape.ROCK, Shape.ROCK): Result.DRAW,
    (Shape.ROCK, Shape.PAPER): Result.WIN,
    (Shape.ROCK, Shape.SCISSORS): Result.LOSS,
    (Shape.PAPER, Shape.ROCK): Result.LOSS,
    (Shape.PAPER, Shape.PAPER): Result.DRAW,
    (Shape.PAPER, Shape.SCISSORS): Result.WIN,
    (Shape.SCISSORS, Shape.ROCK): Result.WIN,
    (Shape.SCISSORS, Shape.PAPER): Result.LOSS,
    (Shape.SCISSORS, Shape.SCISSORS): Result.DRAW,
}


@click.command()
@click.argument(
    "filename",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, readable=True, path_type=Path
    ),
)
def main(filename: Path) -> None:
    total_score = 0
    with filename.open() as f:
        for line in f:
            line = line.strip()
            opponent, player = line.split(" ")
            opponent_shape = OPPONENT_SHAPE_TO_SHAPE[opponent]
            player_shape = Shape(player)
            total_score += SHAPE_SCORES[player_shape]
            total_score += RESULTS[opponent_shape, player_shape]
    click.echo(total_score)


if __name__ == "__main__":
    main()
