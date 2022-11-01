from typing import List
import os
from pathlib import Path
from datetime import datetime

from sneparse.record import SneRecord
from sneparse.definitions import ROOT_DIR

class Catalog:
    def __init__(self, log_file_name: str = "log.txt") -> None:
        self.log_file_path = os.path.join(ROOT_DIR, "resources", "logs", log_file_name)
        self.records: List[SneRecord] = []

        with open(self.log_file_path, "w+") as f:
            f.write(f"[{datetime.now().time()}] Catalog created\n")

    def parse_dir(self, dir_name: str) -> None:
        dir_path = os.path.join(ROOT_DIR, "resources", dir_name)
        
        with open(self.log_file_path, "a+") as f:
            f.write(f"[{datetime.now().time()}] Parsing files in {dir_path}\n")
            for path in Path(dir_path).glob('**/*.json'):
                # TODO: fix that str(path)
                self.records.append(r := SneRecord.from_oac_path(str(path)))
                if len(missing := [k for (k, v) in vars(r).items() if v is None]):
                    f.write(f"[{datetime.now().time()}] Warning: file '{path}' is missing {', '.join(missing)}\n")
