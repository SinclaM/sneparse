#!/usr/bin/env python3
import warnings
from typing import cast
import os
import argparse

from sqlalchemy import URL, create_engine, select
from sqlalchemy.orm import sessionmaker

from aplpy.core import log
from astropy.utils.exceptions import AstropyWarning

from sneparse import RESOURCES
from sneparse.db.models import *
from sneparse.imaging import plot_group, NaNImageError
from sneparse.util import unwrap


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('start', type=int)
    parser.add_argument('count', type=int)

    args = parser.parse_args()

    start = args.start
    count = args.count

    # Turn off warnings from astropy and aplpy
    warnings.simplefilter('ignore', AstropyWarning)
    log.disabled = True

    # Initialize db connection
    engine = create_engine(URL.create(
        drivername=unwrap(os.getenv("DRIVER_NAME")),
        username  =os.getenv("VLASS_USERNAME"),
        password  =os.getenv("VLASS_PASSWORD"),
        host      =os.getenv("VLASS_HOST"),
        database  =os.getenv("VLASS_DATABASE"),
        port      =int(unwrap(os.getenv("VLASS_PORT")))
        ))

    session_maker = sessionmaker(engine)
    session = session_maker()

    select_reps = select(MasterRecord)\
            .filter(MasterRecord.alias_of == None)\
            .filter(MasterRecord.right_ascension != None)\
            .filter(MasterRecord.declination != None)
    select_non_reps = select(MasterRecord)\
            .filter(MasterRecord.alias_of != None)\
            .filter(MasterRecord.right_ascension != None)\
            .filter(MasterRecord.declination != None)

    groups = {row.tuple()[0].id: [row.tuple()[0]] for row in session.execute(select_reps)}
    for row in session.execute(select_non_reps):
        record = row.tuple()[0]
        groups[cast(int, record.alias_of)].append(record)

    with open(RESOURCES.joinpath("logs", "plot_groups_log.txt"), "a") as f:
        for group in [groups[key] for key in sorted(groups.keys())][start:start + count]:
            try:
                fig = plot_group([(cast(float, record.right_ascension),
                                   cast(float, record.declination)) for record in group],
                                 filters="r",
                                 cmap="gray_r")
                file_name = "_".join(record.name for record in group)
                fig.save(RESOURCES.joinpath("images",
                                            f"{len(group) if 1 <= len(group) <= 4 else 'extra'}",
                                            f"{file_name}.png"))
                fig.close()
                f.write(f"[SUCCESS] Plotted {group}.\n")
            except ValueError:
                f.write(f"[FAIL] Sources {group} not in PanSTARRS survery.\n")
            except NaNImageError:
                f.write(f"[FAIL] No image data for {group}.\n")

