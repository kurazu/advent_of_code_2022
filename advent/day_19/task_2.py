import logging
import multiprocessing as mp
import operator
from functools import reduce
from pathlib import Path

import tqdm as tqdm
from returns.curry import partial

from ..cli_utils import wrap_main
from ..logs import setup_logging
from .task_1 import parse_blueprints, score_blueprint

logger = logging.getLogger(__name__)


@wrap_main
def main(filename: Path) -> str:
    blueprints = list(parse_blueprints(filename))[:3]
    score_callback = partial(score_blueprint, time_left=32)
    with mp.Pool(len(blueprints)) as pool:
        scores = tqdm.tqdm(
            pool.imap(score_callback, blueprints, chunksize=1), total=len(blueprints)
        )
        total = reduce(operator.mul, scores)
    return str(total)


if __name__ == "__main__":
    setup_logging(logging.WARNING)
    main()
