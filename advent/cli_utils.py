import functools
from pathlib import Path
from typing import Callable

import click


def wrap_main(main: Callable[[Path], str]) -> Callable[[], None]:
    @functools.wraps(main)
    def main_wrapper(filename: Path) -> None:
        click.echo(main(filename))

    return click.command()(
        click.argument(
            "filename",
            type=click.Path(
                exists=True,
                file_okay=True,
                dir_okay=False,
                readable=True,
                path_type=Path,
            ),
            required=True,
        )(main_wrapper)
    )
