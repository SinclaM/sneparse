from __future__ import annotations # for postponed annotation evaluation
from typing import Tuple, Any, Iterable
from pathlib import Path
from datetime import datetime
import json
from itertools import combinations

# After experimenting with asyncio and threading,
# multiprocessing gave the best speedup by far for mass parsing,
# which I think has to do with Python's GIL.
from multiprocessing import Pool

from sneparse.definitions import ROOT_DIR
from sneparse.record import SneRecord
from sneparse.coordinates import angular_separation


# Using a chunksize > 1 seems to give a slight performance
# boost to imap after testing multiple values.
# The exact value isn't that important.
IMAP_CHUNK_SIZE = 20

NULL_STR = "None"

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

    @classmethod
    def from_lines(cls, lines: Iterable[str], log_file_name: str = "log.txt") -> Catalog:
        """
        Create a `Catalog` from some `lines`, e.g. from a csv file.
        Each line must be formatted as follows:
            `"{name},{ra},{dec},{date},{type},{source}"`
        """
        c = Catalog(log_file_name)

        for line in lines:
            name, ra, dec, date, type_, source = line.split(",")
            ra    = None if ra    == NULL_STR else float(ra)
            dec   = None if dec   == NULL_STR else float(dec)
            date  = None if date  == NULL_STR else datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
            type_ = None if type_ == NULL_STR else type_
            c.records.append(SneRecord(name, ra, dec, date, type_, source))

        return c

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


    def find_close_pairs(self, threshold: float) -> list[Tuple[SneRecord, SneRecord]]:
        """
        Find all pairs of records in `self` separated by no more than
        `angular_separation`. This function is useful for identifying
        records which likely refer to the same source in the sky.
        """
        out: list[Tuple[SneRecord, SneRecord]] = []
        for r1, r2 in combinations(self.records[:1000], r=2):
            if r1.right_ascension is None \
                or r1.declination is None \
                or r2.right_ascension is None \
                or r2.declination is None:
                    continue

            if angular_separation(r1.right_ascension, r1.declination,
                                  r2.right_ascension, r2.declination).degrees < threshold:
                out.append((r1, r2))
        return out

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

