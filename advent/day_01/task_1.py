from pathlib import Path
from typing import Iterable

import click


def read_data(filename: Path) -> Iterable[list[int]]:
    with open(filename, "r", encoding="utf-8") as f:
        buf: list[int] = []
        for line in f:
            line = line.strip()
            if not line:
                yield buf
                buf = []
            else:
                buf.append(int(line))
    yield buf


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
    max_calories = max(calories_per_elf)
    click.echo(max_calories)


if __name__ == "__main__":
    main()
