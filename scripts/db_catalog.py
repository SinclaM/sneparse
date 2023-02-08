#!/usr/bin/env python3
from __future__ import annotations
from typing import cast, Optional
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL
from sqlalchemy import create_engine  
from sqlalchemy import String, Integer, Float, DateTime
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from sneparse.record import SneRecord, Source
from sneparse.catalog import Catalog
from sneparse.coordinates import DecimalDegrees
from sneparse.definitions import ROOT_DIR


def paramterize(r: SneRecord) -> dict:
    return {k: (v.degrees if isinstance(v, DecimalDegrees) else v) for k, v in vars(r).items()}


# declarative base class
class Base(DeclarativeBase):
    pass

class SneRecordWrapper():
    name           : Mapped[str]                = mapped_column(String)
    right_ascension: Mapped[Optional[float]]    = mapped_column(Float, nullable=True)
    declination    : Mapped[Optional[float]]    = mapped_column(Float, nullable=True)
    discover_date  : Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)
    claimed_type   : Mapped[Optional[str]]      = mapped_column(String, nullable=True)
    source         : Mapped[str]                = mapped_column(String)

class UncleanedRecord(Base, SneRecordWrapper):
    __tablename__ = "test"
    
    pk: Mapped[int] = mapped_column(Integer, primary_key=True)


if __name__ == "__main__":
    load_dotenv()

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
