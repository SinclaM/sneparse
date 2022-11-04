from typing import Tuple, Any
from pathlib import Path
from datetime import datetime
import json

# After experimenting with asyncio and threading,
# multiprocessing gave the best speedup by far for mass parsing,
# which I think has to do with Python's GIL.
from multiprocessing import Pool

from sneparse.record import SneRecord
from sneparse.definitions import ROOT_DIR


# Using a chunksize > 1 seems to give a slight performance
# boost to imap after testing multiple values.
# The exact value isn't that important.
IMAP_CHUNK_SIZE = 20

class Catalog:
    """
    A `Catalog` holds a collection of `SneRecord` objects. It manages a log file
    to record warnings.
    """
    def __init__(self, log_file_name: str = "log.txt") -> None:
        self.log_file_path = Path(ROOT_DIR).joinpath("resources", "logs", log_file_name)
        self.records: list[SneRecord] = []

        with open(self.log_file_path, "w+") as f:
            f.write(f"[{datetime.now().time()}] Catalog created\n")

    def parse_dir(self, dir_path: Path, num_processes: int = 12) -> None:
        """
        Recursively parse all json files in a directory into a `Catalog`'s
        records. Multiple processes can be used for a perfomance boost on
        a multicore system. For best perfomance, `num_processes` should
        equal the number of cores.
        """
        with open(self.log_file_path, "a+") as f:
            f.write(f"[{datetime.now().time()}] Parsing files in {dir_path}\n")

            # Recursively find all json files in the specified directory.
            paths = Path(dir_path).glob("**/*.json")
            pool = Pool(num_processes)

            # Parse each record. Files are split among multiple processes for
            # an easy speedup to this loop.
            for r, path in pool.imap_unordered(worker, paths, IMAP_CHUNK_SIZE):
                self.records.append(r)

                # If any of the fields in the newly parsed record have a value
                # of None, then put a warning in the log file.
                if len(missing := [k for (k, v) in vars(r).items() if v is None]):
                    f.write(f"[{datetime.now().time()}] Warning: file '{path}' is missing {', '.join(missing)}\n")

            # Clean up
            pool.close()
            pool.join()

# This function must be top-leveled defined so that in can be pickled and used
# with the multiprocessing pool.
def worker(path: Path) -> Tuple[SneRecord, Path]:
    """
    Create an `SneRecord` from a json file at a given `path`.
    """
    d: dict[str, Any]
    with open(path, "r") as f:
        d = json.load(f)

    # The path is passed back in the return value so that the caller can access
    # it for logging purposes. There might be a better way to do this.
    return (SneRecord.from_oac(d), path)

