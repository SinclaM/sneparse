#!/usr/bin/env python3
from __future__ import annotations
from typing import cast, Optional, Iterator
import os
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass

from sqlalchemy import URL, ForeignKey, text, create_engine, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import sessionmaker, DeclarativeBase, aliased
from disjoint_set import DisjointSet

from sneparse.record import SneRecord, Source
from sneparse.catalog import Catalog
from sneparse.coordinates import DecimalDegrees
from sneparse.definitions import ROOT_DIR

MASTER_TABLE_NAME = "master"

def paramterize(r: SneRecord) -> dict:
    return {k: (v.degrees if isinstance(v, DecimalDegrees) else v) for k, v in vars(r).items()}

class Base(DeclarativeBase):
    pass

@dataclass
class SneRecordWrapper():
    name           : Mapped[str]
    right_ascension: Mapped[Optional[float]]
    declination    : Mapped[Optional[float]]
    discover_date  : Mapped[Optional[datetime]]
    claimed_type   : Mapped[Optional[str]]
    source         : Mapped[Source]

@dataclass
class MasterRecord(Base, SneRecordWrapper):
    __tablename__ = MASTER_TABLE_NAME
    
    id      : Mapped[int]           = mapped_column(primary_key=True)
    alias_of: Mapped[Optional[int]] = mapped_column(ForeignKey(f"{MASTER_TABLE_NAME}.id"), default=None)

    def __hash__(self) -> int:
        return hash(repr(self))


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
        session.add(MasterRecord(**paramterize(record)))
    session.commit()

    with engine.connect() as con:
        con.execute(text(
            f"""
            CREATE INDEX ON {MASTER_TABLE_NAME} (q3c_ang2ipix(right_ascension, declination));
            CLUSTER {MASTER_TABLE_NAME}_q3c_ang2ipix_idx ON {MASTER_TABLE_NAME};
            ANALYZE {MASTER_TABLE_NAME};
            """
        ))
        con.commit()

    alias = aliased(MasterRecord)
    cross_matches = session \
                .query(MasterRecord, alias) \
                .filter(func.q3c_join(MasterRecord.right_ascension,
                                      MasterRecord.declination,
                                      alias.right_ascension,
                                      alias.declination,
                                      0.000555556)) \
                .where((MasterRecord.name < alias.name) & 
                        (timedelta(0) < (MasterRecord.discover_date - alias.discover_date)) &
                        ((MasterRecord.discover_date - alias.discover_date) < timedelta(1))) \
                .all()

    ds: DisjointSet[MasterRecord] = DisjointSet()
    for u, v in [row.tuple() for row in cross_matches]:
        ds.union(u, v)

    for s in cast(Iterator[set[MasterRecord]], ds.itersets()):
        records = list(s)
        rep_idx = next((i for i, record in enumerate(records) if record.source == Source.TNS), 0)
        for i, record in enumerate(records):
            if i != rep_idx:
                record.alias_of = records[rep_idx].id

    session.commit()
