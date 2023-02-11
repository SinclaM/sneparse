#!/usr/bin/env python3
from __future__ import annotations
from typing import cast, Optional, Iterator, Any
import os
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass

from sqlalchemy import URL, ForeignKey, text, create_engine, func, select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import sessionmaker, DeclarativeBase, aliased
from disjoint_set import DisjointSet

from sneparse.record import SneRecord, Source
from sneparse.catalog import Catalog
from sneparse.coordinates import DecimalDegrees
from sneparse.definitions import ROOT_DIR

MASTER_TABLE_NAME = "master"

def paramterize(r: SneRecord) -> dict[str, Any]:
    """
    Construct the dictionary to be used as the parameters for the __init__ of
    an SQLAlchemy row class. Essentialy just `vars(r)` but converts the
    fields of type `DecimalDegrees` to `float`.
    """
    return {k: (v.degrees if isinstance(v, DecimalDegrees) else v) for k, v in vars(r).items()}

class Base(DeclarativeBase):
    """
    Base class for declarative ORM.
    """
    pass

@dataclass
class SneRecordWrapper():
    """
    Wrapper around an `SneRecord` to be used with SQLAlchemy. To be inherited
    by other classes.
    """
    name           : Mapped[str]
    right_ascension: Mapped[Optional[float]]
    declination    : Mapped[Optional[float]]
    discover_date  : Mapped[Optional[datetime]]
    claimed_type   : Mapped[Optional[str]]
    source         : Mapped[Source]

@dataclass
class MasterRecord(Base, SneRecordWrapper):
    """
    A row in the table of all records.
    """
    __tablename__ = MASTER_TABLE_NAME
    
    id      : Mapped[int]           = mapped_column(primary_key=True)
    alias_of: Mapped[Optional[int]] = mapped_column(ForeignKey(f"{MASTER_TABLE_NAME}.id"), default=None)

    def __hash__(self) -> int:
        return hash(repr(self))


if __name__ == "__main__":
    # Initialize Postgres connection
    engine = create_engine(URL.create(
        drivername=cast(str, os.getenv("DRIVER_NAME")),
        username=os.getenv("USERNAME"),
        password=os.getenv("PASSWORD"),
        host    =os.getenv("HOST"),
        database=os.getenv("DATABASE")
    ))

    Session = sessionmaker(engine)  
    session = Session()

    # Drop all the tables that descend from `Base` and re-create them from scratch
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    # Create a catalog from data sources
    c = Catalog()

    # TODO: is it really necessary to construct the entire catalog in memory,
    # only to add it all to the database and never use it again? It would
    # probably be better to insert right away after parsing.
    N_PROCESSES = 12
    c.parse_dir(Path(ROOT_DIR).joinpath("resources", "oac-data"), Source.OAC, N_PROCESSES)
    c.parse_dir(Path(ROOT_DIR).joinpath("resources", "tns-data"), Source.TNS, N_PROCESSES)

    # Insert records into master table
    for record in c.records:
        session.add(MasterRecord(**paramterize(record)))
    session.commit()

    # Prepare the table for fast cross matching
    # TODO: can this be done without raw SQL?
    session.execute(text(
        f"""
        CREATE INDEX ON {MASTER_TABLE_NAME} (q3c_ang2ipix(right_ascension, declination));
        CLUSTER {MASTER_TABLE_NAME}_q3c_ang2ipix_idx ON {MASTER_TABLE_NAME};
        ANALYZE {MASTER_TABLE_NAME};
        """
    ))
    session.commit()

    # Perform the cross matching
    aliasMasterRecord = aliased(MasterRecord)
    select_pairs = \
        select(MasterRecord, aliasMasterRecord) \
            .filter(func.q3c_join(MasterRecord.right_ascension,
                                  MasterRecord.declination,
                                  aliasMasterRecord.right_ascension,
                                  aliasMasterRecord.declination,
                                  0.000555556)) \
            .where((MasterRecord.name < aliasMasterRecord.name) & 
                   (timedelta(0) < (MasterRecord.discover_date - aliasMasterRecord.discover_date)) &
                   ((MasterRecord.discover_date - aliasMasterRecord.discover_date) < timedelta(1)))
    cross_matches = session.execute(select_pairs).all()

    # Combine matches into disjoint sets of 2, 3, 4, ...
    ds: DisjointSet[MasterRecord] = DisjointSet()
    for u, v in [row.tuple() for row in cross_matches]:
        ds.union(u, v)

    # Assign a representative member in each set and update the table
    # so that the other members point to it via the `alias_of` foreign key
    for s in cast(Iterator[set[MasterRecord]], ds.itersets()):
        records = list(s)

        # TODO: the best records are the ones from TNS with the most information
        # (e.g. `claimed_type` not NULL). Use a cost function to evaluate each member
        # and choose the best as the representative.
        rep_idx = next((i for i, record in enumerate(records) if record.source == Source.TNS), 0)
        for i, record in enumerate(records):
            if i != rep_idx:
                record.alias_of = records[rep_idx].id
    session.commit()
