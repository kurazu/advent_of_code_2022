import logging
import sys

from . import __name__ as package_name


def setup_logging(package_log_level: int = logging.DEBUG) -> None:
    logging.basicConfig(
        level=logging.WARNING,
        format="[%(asctime)s][%(levelname)8s][%(name)s] %(message)s",
        stream=sys.stdout,
    )
    for logger_name, level in {
        package_name: package_log_level,
        "__main__": package_log_level,
    }.items():
        logging.getLogger(logger_name).setLevel(level)
