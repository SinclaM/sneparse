#!/usr/bin/env python3
import warnings
from typing import cast
import os

from sqlalchemy import URL, create_engine, select
from sqlalchemy.orm import sessionmaker
import matplotlib.pyplot as plt

from aplpy.core import log
from astropy.utils.exceptions import AstropyWarning


from sneparse.db.models import *
from sneparse.imaging import plot_group
from sneparse.util import unwrap

if __name__ == "__main__":
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
        groups[cast(int, record.alias_of)].append(record)

    for group in list(groups.values())[:10]:
        fig = plot_group([(cast(float, record.right_ascension), cast(float, record.declination)) for record in group],
                         filters="r",
                         cmap="gray_r")
        file_name = "_".join(record.name for record in group)
        fig.save(f"{file_name}.png")


