from enum import Enum
from pathlib import Path

import click

from .task_1 import OPPONENT_SHAPE_TO_SHAPE, SHAPE_SCORES, Shape


class Result(str, Enum):
    WIN = "Z"
    DRAW = "Y"
    LOSS = "X"


PLAYS: dict[tuple[Shape, Result], Shape] = {
    (Shape.ROCK, Result.WIN): Shape.PAPER,
    (Shape.ROCK, Result.DRAW): Shape.ROCK,
    (Shape.ROCK, Result.LOSS): Shape.SCISSORS,
    (Shape.PAPER, Result.WIN): Shape.SCISSORS,
    (Shape.PAPER, Result.DRAW): Shape.PAPER,
    (Shape.PAPER, Result.LOSS): Shape.ROCK,
    (Shape.SCISSORS, Result.WIN): Shape.ROCK,
    (Shape.SCISSORS, Result.DRAW): Shape.SCISSORS,
    (Shape.SCISSORS, Result.LOSS): Shape.PAPER,
}

RESULT_SCORES: dict[Result, int] = {
    Result.WIN: 6,
    Result.DRAW: 3,
    Result.LOSS: 0,
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
            opponent, required_result = line.split(" ")
            opponent_shape = OPPONENT_SHAPE_TO_SHAPE[opponent]
            result = Result(required_result)
            player_shape = PLAYS[opponent_shape, result]
            total_score += SHAPE_SCORES[player_shape]
            total_score += RESULT_SCORES[result]
    click.echo(total_score)


if __name__ == "__main__":
    main()
