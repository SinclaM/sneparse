#!/usr/bin/env python3
from typing import Iterator, cast
from pathlib import Path
import csv
from io import TextIOWrapper

from disjoint_set import DisjointSet

from sneparse.definitions import ROOT_DIR
from sneparse.catalog import Catalog
from sneparse.record import SneRecord
from sneparse.coordinates import DecimalDegrees

NULL_STR = "None"

def independent_sets(path: Path) -> Iterator[set[SneRecord]]:
    c: Catalog
    ds: DisjointSet[SneRecord] = DisjointSet()

    with open(path) as f:
        # Skip the first line with the column names
        next(f)
        c = Catalog.from_lines(f)

    for u, v in c.find_close_pairs(DecimalDegrees(0.000555556)):
        if u.discover_date is not None and v.discover_date is not None:
            if abs(u.discover_date - v.discover_date).days < 1:
                ds.union(u, v)
    return cast(Iterator[set[SneRecord]], ds.itersets())


if __name__ == "__main__":
    with (
        open(Path(ROOT_DIR).joinpath("resources", "cleaned.csv"), "w") as cleaned,
        open(Path(ROOT_DIR).joinpath("resources", "dupes.csv"), "w") as dupes
    ):
        for s in independent_sets(Path(ROOT_DIR).joinpath("resources", "sne.csv")):
            if len(s) > 1:
                print("\n".join(str(r) for r in s))
                print()
