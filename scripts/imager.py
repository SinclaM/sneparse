#!/usr/bin/env python3
import os

from sqlalchemy import URL, create_engine, func, select
from sqlalchemy.orm import sessionmaker
import matplotlib.pyplot as plt

from sneparse.imaging import plot_image_astropy, plot_image_apl
from sneparse.db.models import CleanedRecord
from sneparse.util import unwrap
 
if __name__ == "__main__":
    engine = create_engine(URL.create(
        drivername=unwrap(os.getenv("DRIVER_NAME")),
        username  =os.getenv("ASTRO_USERNAME"),
        password  =os.getenv("ASTRO_PASSWORD"),
        host      =os.getenv("ASTRO_HOST"),
        database  =os.getenv("ASTRO_DATABASE")
    ))

    session_maker = sessionmaker(engine)  
    session = session_maker()

    # TODO: don't sequentially scan entire table
    select_random = select(CleanedRecord.name, CleanedRecord.right_ascension, CleanedRecord.declination)\
                        .order_by(func.random())\
                        .limit(1)
    name, ra, dec = unwrap(session.execute(select_random).first()).tuple()

    print(f"""Plotting source "{name}" (ra={ra}, dec={dec})""")
    plot_image_astropy(ra, dec, cmap="gray_r", filters="r")

    plot_image_apl(ra, dec, cmap="gray_r", filters="r")

    plt.show()
