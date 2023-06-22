#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import time
import csv

from sneparse import RESOURCES
from sneparse.catalog import Catalog
from sneparse.record import SneRecord, Source

if __name__ == "__main__":

    start_time = time.time()

    N_PROCESSES = 12

    c = Catalog()

    c.parse_dir(RESOURCES.joinpath("oac-data"), Source.OAC, N_PROCESSES)
    c.parse_dir(RESOURCES.joinpath("tns-data"), Source.TNS, N_PROCESSES)

    with open(RESOURCES.joinpath("sne.csv"), "w") as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(("name", "ra", "dec",
                          "discovery_date", "claimed_type", "source"))
        writer.writerows(map(SneRecord.as_row, c.records))

    print(f"------{time.time() - start_time}--------")
