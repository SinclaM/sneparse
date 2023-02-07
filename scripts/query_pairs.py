#!/usr/bin/env python3
from pathlib import Path

from disjoint_set import DisjointSet

from sneparse.definitions import ROOT_DIR
from sneparse.catalog import Catalog
from sneparse.record import Source
from sneparse.coordinates import DecimalDegrees

NULL_STR = "None"

if __name__ == "__main__":

    with open(Path(ROOT_DIR).joinpath("resources", "sne.csv"), "r") as csvfile:
        # Skip the first line with the column names
        next(csvfile)

        c = Catalog.from_lines(csvfile)
        ds = DisjointSet()
        for u, v in c.find_close_pairs(DecimalDegrees(0.000555556)):
            if u.discover_date is not None and v.discover_date is not None:
                if abs(u.discover_date - v.discover_date).days < 1:
                    ds.union(u, v)

        # for s in ds.itersets():
            # if len(s) > 1:
                # print("\n".join(str(r) for r in s))
                # print()

        for s in ds.itersets():
            if len({r for r in s if r.source == Source.TNS}) > 1:
                print("\n".join(str(r) for r in s))
                print()
