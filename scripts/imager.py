import os

from sqlalchemy import URL, create_engine, func, select
from sqlalchemy.orm import sessionmaker

from sneparse.imaging import plot_image
from sneparse.db.models import *
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

    stmt = select(CleanedRecord.right_ascension, CleanedRecord.declination).order_by(func.random())
    ra, dec = unwrap(session.execute(stmt).first()).tuple()

    plot_image(ra, dec)
