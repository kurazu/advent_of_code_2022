from pathlib import Path
from typing import Callable

import click


def wrap_main(main: Callable[[Path], str]) -> Callable[[], None]:
    wrapped_main = click.command()(
        click.argument(
            "filename",
            type=click.Path(
                exists=True,
                file_okay=True,
                dir_okay=False,
                readable=True,
                path_type=Path,
            ),
        )(main)
    )
    return wrapped_main
