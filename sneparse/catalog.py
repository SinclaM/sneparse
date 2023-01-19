from __future__ import annotations # for postponed annotation evaluation
from typing import Tuple, Any, Iterable, Callable
from pathlib import Path
from datetime import datetime
import json
import csv

# After experimenting with asyncio and threading,
# multiprocessing gave the best speedup by far for mass parsing,
# which I think has to do with Python's GIL.
from multiprocessing import Pool
from scipy.spatial import KDTree

from sneparse.definitions import ROOT_DIR
from sneparse.record import SneRecord, Source
from sneparse.coordinates import Cartesian, angular_separation_to_distance, DecimalDegrees


# Using a chunksize > 1 seems to give a slight performance
# boost to imap after testing multiple values.
# The exact value isn't that important.
IMAP_CHUNK_SIZE = 20

NULL_STR = ""

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
            ra     = None if ra    == NULL_STR else float(ra)
            dec    = None if dec   == NULL_STR else float(dec)
            date   = None if date  == NULL_STR else datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f")
            type_  = None if type_ == NULL_STR else type_
            source = source.replace("\n", "")
            c.records.append(SneRecord(name, ra, dec, date, type_, Source.from_str(source)))

        return c

    def _parse_dir_base(self,
                        dir_path: Path,
                        worker: Callable[[Path], Tuple[list[SneRecord], Path]],
                        pattern: str,
                        num_processes: int = 12) -> None:
        with open(self.log_file_path, "a+") as f:
            f.write(f"[{datetime.now().time()}] Parsing files in {dir_path}\n")

            # Recursively find all json files in the specified directory.
            paths = Path(dir_path).glob(pattern)
            pool = Pool(num_processes)

            # Parse each record. Files are split among multiple processes for
            # an easy speedup to this loop.
            for records, path in pool.imap_unordered(worker, paths, IMAP_CHUNK_SIZE):
                self.records.extend(records)

                for r in records:
                    # The unclassified TNS data will naturaly be missing a claimed type.
                    # We set it to `None` instead of the empty string for consistency.
                    if r.claimed_type == "":
                        r.claimed_type = None

                    # If any of the fields in the newly parsed record are empty,
                    # then put a warning in the log file.
                    if len(missing := [k for (k, v) in vars(r).items() if v is None]):
                        f.write(f"[{datetime.now().time()}] Warning: In '{path}','{r.name}' is missing {', '.join(missing)}\n")

            # Clean up
            pool.close()
            pool.join()

    def parse_dir(self, dir_path: Path, source: Source, num_processes: int = 12) -> None:
        """
        Recursively parse all json files in a directory into a `Catalog`'s
        records. Multiple processes can be used for a perfomance boost on
        a multicore system. For best perfomance, `num_processes` should
        equal the number of cores.
        """
        match source:
            case Source.OAC:
                self._parse_dir_base(dir_path, _parse_dir_oac_worker, "**/*.json", num_processes);
            case Source.TNS:
                self._parse_dir_base(dir_path, _parse_dir_tns_worker, "**/*.tsv", num_processes);
            case _:
                raise Exception(f"Unknown source: {source}")



    def find_close_pairs(self, threshold: DecimalDegrees) -> list[Tuple[SneRecord, SneRecord]]:
        """
        Find all pairs of records in `self` separated by no more than
        `threshold`. This function is useful for identifying
        records which likely refer to the same source in the sky.
        """

        valid_records = [r for r in self.records if r.right_ascension is not None and r.declination is not None]

        distance_threshold = angular_separation_to_distance(threshold)

        # The typechecker will complain on the call to KDTree if `points` is allowed
        # the type of list[Tuple[ ... ]] because apparently it isn't `ArrayLike` (Why not??).
        # So we set it to list[Any].
        points: list[Any] = [((c := Cartesian.from_angular(r.right_ascension, r.declination)).x, c.y, c.z) \
                for r in valid_records]


        kd_tree = KDTree(points)
        return [(valid_records[i], valid_records[j]) for (i, j) in kd_tree.query_pairs(distance_threshold)]

# This function must be top-level defined so that in can be pickled and used
# with the multiprocessing pool.
def _parse_dir_oac_worker(path: Path) -> Tuple[list[SneRecord], Path]:
    """
    Create an `SneRecord` from an OAC json file at a given `path`.
    """
    d: dict[str, Any]
    with open(path, "r") as f:
        d = json.load(f)

    # The path is passed back in the return value so that the caller can access
    # it for logging purposes. There might be a better way to do this.
    return ([SneRecord.from_oac(d)], path)

# This function must be top-level defined so that in can be pickled and used
# with the multiprocessing pool.
def _parse_dir_tns_worker(path: Path) -> Tuple[list[SneRecord], Path]:
    """
    Create an `SneRecord` from a TNS tsv file at a given `path`.
    """
    with open(path, "r") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return (SneRecord.from_tns(reader), path)

