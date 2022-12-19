import logging
from pathlib import Path

from ..cli_utils import wrap_main
from ..logs import setup_logging

logger = logging.getLogger(__name__)


@wrap_main
def main(filename: Path) -> str:
    return ""


if __name__ == "__main__":
    setup_logging()
    main()
