#!/usr/bin/env python3
from pathlib import Path
import time
import csv

from sneparse.definitions import ROOT_DIR
from sneparse.catalog import Catalog
from sneparse.record import SneRecord


if __name__ == "__main__":

    start_time = time.time()

    N_PROCESSES = 12

    c = Catalog()
    c.parse_dir(Path(ROOT_DIR).joinpath("resources", "oac-data"), N_PROCESSES)

    with open(Path(ROOT_DIR).joinpath("resources", "oac-sne.csv"), "w") as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(("Name", "Right Ascension", "Declination",
                          "Discovery Date", "Claimed Type", "Source"))
        writer.writerows(map(SneRecord.as_row, c.records))

    print(f"------{time.time() - start_time}--------")
