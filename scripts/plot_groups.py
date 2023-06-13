#!/usr/bin/env python3
import warnings
from typing import cast
import os
from pathlib import Path

from sqlalchemy import URL, create_engine, select
from sqlalchemy.orm import sessionmaker
import matplotlib.pyplot as plt

from aplpy.core import log
from astropy.utils.exceptions import AstropyWarning

from sneparse.db.models import *
from sneparse.imaging import plot_group, NaNImageError
from sneparse.util import unwrap

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('start', type=int,  help='an integer')
    parser.add_argument('stop',  type=int,  help='an integer')
    parser.add_argument('folder',type=int, help='an integer')

    args = parser.parse_args()

    start  = args.start
    stop   = args.stop
    folder = args.folder
    # Turn off warnings from astropy and aplpy
    warnings.simplefilter('ignore', AstropyWarning)
    log.disabled = True

    # Initialize db connection
    engine = create_engine(URL.create(
        drivername=unwrap(os.getenv("DRIVER_NAME")),
        username  =os.getenv("USERNAME"),
        password  =os.getenv("PASSWORD"),
        host      =os.getenv("HOST"),
        database  =os.getenv("DATABASE")
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
        groups[int(record.alias_of)].append(record)

    Path(f"sneparse/resources/images/{folder}").mkdir(exist_ok=True)
    with open(f"sneparse/resources/log_{folder}.txt", "w") as f:
        for group in [groups[key] for key in sorted(groups.keys())][start:stop]:
            try:
                fig = plot_group([(cast(float, record.right_ascension), cast(float, record.declination)) for record in group],
                                 filters="r",
                                 cmap="gray_r")
                file_name = "_".join(record.name for record in group)
                fig.save(f"sneparse/resources/images/{folder}/{file_name}.png")
                plt.clf()
                plt.close()
                f.write(f"[SUCCESS] Plotted {group}.\n")
            except ValueError:
                f.write(f"[FAIL] Sources {group} not in PanSTARRS survery.\n")
            except NaNImageError:
                f.write(f"[FAIL] No image data for {group}.\n")
