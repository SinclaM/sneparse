#!/usr/bin/env python3
import os
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy import URL, create_engine, select
from sqlalchemy.orm import sessionmaker
from disjoint_set import DisjointSet

from sneparse.util import unwrap
from sneparse.db.models import *


renamings = DisjointSet({
    None: "Unknown",
    "Ia": "SN Ia",
    "II": "SN II",
    "Ib": "SN Ib",
    "Ic": "SN Ic",
    "II P": "SN IIP",
    "IIb": "SN IIb",
    "IIn": "SN IIn",
})

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    args = parser.parse_args()

    engine = create_engine(URL.create(
        drivername=unwrap(os.getenv("DRIVER_NAME")),
        username  =os.getenv("TRANSIENTS_USERNAME"),
        password  =os.getenv("TRANSIENTS_PASSWORD"),
        host      =os.getenv("TRANSIENTS_HOST"),
        database  ="vlass",
        port      =int(unwrap(os.getenv("TRANSIENTS_PORT")))
    ))

    session_maker = sessionmaker(engine)


    with session_maker() as session:
        all_records = list(map(lambda r: r._tuple()[0], session.execute(select(CleanedRecord)).all()))

    cross_matches_names = set(file.stem for file in args.path.glob("**/*.png"))

    records = pd.DataFrame(
        { k: v for (k, v) in vars(r).items() if not k.startswith("_") }
            for r in all_records if r.name in cross_matches_names
    )

    counts = records["claimed_type"].value_counts(dropna=False)
    cleaned_counts = counts.groupby(lambda s: renamings.find(s)).sum().sort_values(ascending=False)

    cleaned_counts.plot(kind="bar")
    plt.show()

