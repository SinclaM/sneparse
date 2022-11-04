from typing import Tuple, Any
from pathlib import Path
from datetime import datetime
import json
from multiprocessing import Pool

from sneparse.record import SneRecord
from sneparse.definitions import ROOT_DIR


class Catalog:
    def __init__(self, log_file_name: str = "log.txt") -> None:
        self.log_file_path = Path(ROOT_DIR).joinpath("resources", "logs", log_file_name)
        self.records: list[SneRecord] = []

        with open(self.log_file_path, "w+") as f:
            f.write(f"[{datetime.now().time()}] Catalog created\n")

    def parse_dir(self, dir_path: Path, num_processes: int = 12) -> None:

        with open(self.log_file_path, "a+") as f:
            f.write(f"[{datetime.now().time()}] Parsing files in {dir_path}\n")
            paths = Path(dir_path).glob("**/*.json")
            pool = Pool(num_processes)
            for r, path in pool.imap_unordered(helper, paths, 20):
                self.records.append(r)
                if len(missing := [k for (k, v) in vars(r).items() if v is None]):
                    f.write(f"[{datetime.now().time()}] Warning: file '{path}' is missing {', '.join(missing)}\n")
            pool.close()
            pool.join()

# TODO: Make this a lambda in parse_dir. For now its a top level function
#       so that pickling works with multiprocessing
def helper(path: Path) -> Tuple[SneRecord, Path]:
    d: dict[str, Any]
    with open(path, "r") as f:
        d = json.load(f)
    return (SneRecord.from_oac(d), path)

