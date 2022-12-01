import heapq
from pathlib import Path

import click

from .task_1 import read_data


@click.command()
@click.argument(
    "filename",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, readable=True, path_type=Path
    ),
)
def main(filename: Path) -> None:
    snacks_per_elf = read_data(filename)
    calories_per_elf = map(sum, snacks_per_elf)
    three_best = heapq.nlargest(3, calories_per_elf)
    three_sum = sum(three_best)
    click.echo(three_sum)


if __name__ == "__main__":
    main()
