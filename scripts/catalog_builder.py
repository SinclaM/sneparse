#!/usr/bin/env python3
from pathlib import Path
from sneparse.definitions import ROOT_DIR
from sneparse.catalog import Catalog

import time

if __name__ == "__main__":

    start_time = time.time()

    N_PROCESSES = 12

    c = Catalog()
    c.parse_dir(Path(ROOT_DIR).joinpath("resources", "oac-data"), N_PROCESSES)

    for record in c.records:
        print(record)

    print(f"------{time.time() - start_time}--------")
