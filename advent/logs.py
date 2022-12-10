import logging

from . import __name__ as package_name


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.WARNING,
        format="[%(asctime)s][%(levelname)8s][%(name)s] %(message)s",
    )
    for logger_name, level in {
        package_name: logging.DEBUG,
        "__main__": logging.DEBUG,
    }.items():
        logging.getLogger(logger_name).setLevel(level)
