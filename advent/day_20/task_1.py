import logging
from pathlib import Path
from typing import Iterable

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines
from ..logs import setup_logging

logger = logging.getLogger(__name__)


def read_numbers(filename: Path) -> Iterable[int]:
    return map(int, get_stripped_lines(filename))


@wrap_main
def main(filename: Path) -> str:
    numbers = list(read_numbers(filename))
    logger.debug("Read %d numbers", len(numbers))
    return ""


if __name__ == "__main__":
    setup_logging()
    main()
