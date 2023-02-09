#!/usr/bin/env python3
from __future__ import annotations
from typing import cast, Optional
import os
from pathlib import Path
from datetime import datetime

from sqlalchemy import URL, text
from sqlalchemy import create_engine  
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from sneparse.record import SneRecord, Source
from sneparse.catalog import Catalog
from sneparse.coordinates import DecimalDegrees
from sneparse.definitions import ROOT_DIR

UNCLEANED_TABLE_NAME = "uncleaned"

def paramterize(r: SneRecord) -> dict:
    return {k: (v.degrees if isinstance(v, DecimalDegrees) else v) for k, v in vars(r).items()}

class Base(DeclarativeBase):
    pass

class SneRecordWrapper():
    name           : Mapped[str]
    right_ascension: Mapped[Optional[float]]
    declination    : Mapped[Optional[float]]
    discover_date  : Mapped[Optional[datetime]]
    claimed_type   : Mapped[Optional[str]]
    source         : Mapped[Source]

class UncleanedRecord(Base, SneRecordWrapper):
    __tablename__ = UNCLEANED_TABLE_NAME
    
    id: Mapped[int] = mapped_column(primary_key=True)


if __name__ == "__main__":
    engine = create_engine(URL.create(
        drivername=cast(str, os.getenv("DRIVER_NAME")),
        username=os.getenv("USERNAME"),
        password=os.getenv("PASSWORD"),
        host    =os.getenv("HOST"),
        database=os.getenv("DATABASE")
    ))

    Session = sessionmaker(engine)  
    session = Session()

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    N_PROCESSES = 12

    c = Catalog()

    c.parse_dir(Path(ROOT_DIR).joinpath("resources", "oac-data"), Source.OAC, N_PROCESSES)
    c.parse_dir(Path(ROOT_DIR).joinpath("resources", "tns-data"), Source.TNS, N_PROCESSES)

    for record in c.records:
        session.add(UncleanedRecord(**paramterize(record)))
    session.commit()

    with engine.connect() as con:
        con.execute(text(
            f"""
            CREATE INDEX ON {UNCLEANED_TABLE_NAME} (q3c_ang2ipix(right_ascension, declination));
            CLUSTER {UNCLEANED_TABLE_NAME}_q3c_ang2ipix_idx ON {UNCLEANED_TABLE_NAME};
            ANALYZE {UNCLEANED_TABLE_NAME};
            """
        ))
        con.commit()
