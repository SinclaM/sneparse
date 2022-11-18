#!/usr/bin/env python3
from pathlib import Path

from sneparse.definitions import ROOT_DIR
from sneparse.catalog import Catalog
from sneparse.coordinates import DecimalDegrees

from datetime import timedelta

NULL_STR = "None"

if __name__ == "__main__":

    with open(Path(ROOT_DIR).joinpath("resources", "oac-sne.csv"), "r") as csvfile:
        # Skip the first line with the column names
        next(csvfile)

        c = Catalog.from_lines(csvfile)
        for u, v in c.find_close_pairs(DecimalDegrees(0.38889)):
            if u.discover_date is not None and v.discover_date is not None:
                if u.discover_date == v.discover_date:
                    print("WOW!!!!!!!")
            print(u)
            print(v)
            print()
