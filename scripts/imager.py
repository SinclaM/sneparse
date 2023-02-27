import os

from sqlalchemy import URL, create_engine, func, select
from sqlalchemy.orm import sessionmaker

from sneparse.imaging import plot_image
from sneparse.db.models import CleanedRecord
from sneparse.util import unwrap
 
if __name__ == "__main__":
    engine = create_engine(URL.create(
        drivername=unwrap(os.getenv("DRIVER_NAME")),
        username  =os.getenv("USERNAME"),
        password  =os.getenv("PASSWORD"),
        host      =os.getenv("HOST"),
        database  =os.getenv("DATABASE")
    ))

    session_maker = sessionmaker(engine)  
    session = session_maker()

    select_random = select(CleanedRecord.name, CleanedRecord.right_ascension, CleanedRecord.declination)\
                        .order_by(func.random())
    name, ra, dec = unwrap(session.execute(select_random).first()).tuple()

    print(f"""Plotting source "{name}" (ra={ra}, dec={dec})""")

    plot_image(ra, dec)
