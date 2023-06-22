#!/usr/bin/env python3
from __future__ import annotations
from typing import cast, Iterator
import os
from pathlib import Path
from datetime import timedelta

from sqlalchemy import URL, create_engine, func, select
from sqlalchemy.orm import sessionmaker, aliased
from disjoint_set import DisjointSet

from sneparse import RESOURCES
from sneparse.coordinates import DecimalDegrees, DegreesMinutesSeconds
from sneparse.record import Source
from sneparse.catalog import Catalog
from sneparse.db.models import *
from sneparse.db.util import paramterize, prepare_q3c_index
from sneparse.util import unwrap

if __name__ == "__main__":
    # Initialize Postgres connection
    engine = create_engine(URL.create(
        drivername=unwrap(os.getenv("DRIVER_NAME")),
        username  =os.getenv("ASTRO_USERNAME"),
        password  =os.getenv("ASTRO_PASSWORD"),
        host      =os.getenv("ASTRO_HOST"),
        database  =os.getenv("ASTRO_DATABASE")
    ))

    session_maker = sessionmaker(engine)  
    session = session_maker()

    # Drop all the tables that descend from `Base` and re-create them from scratch
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    # Create a catalog from data sources
    c = Catalog()

    # TODO: is it really necessary to construct the entire catalog in memory,
    # only to add it all to the database and never use it again? It would
    # probably be better to insert right away after parsing.
    N_PROCESSES = 12
    c.parse_dir(RESOURCES.joinpath("oac-data"), Source.OAC, N_PROCESSES)
    c.parse_dir(RESOURCES.joinpath("tns-data"), Source.TNS, N_PROCESSES)

    # Insert records into master table
    for record in c.records:
        session.add(MasterRecord(**paramterize(record)))
    session.commit()

    prepare_q3c_index(MASTER_TABLE_NAME, session)
    session.commit()

    # Perform the cross matching
    separation = DecimalDegrees.from_dms(DegreesMinutesSeconds(1, 0, 0, 5)).degrees

    # TODO: clean up the `where` clause. There has to be a simpler
    # way to get make a comparison with the absolute value of an interval.
    aliasMasterRecord = aliased(MasterRecord)
    select_pairs = \
        select(MasterRecord, aliasMasterRecord) \
            .filter(func.q3c_join(MasterRecord.right_ascension,
                                  MasterRecord.declination,
                                  aliasMasterRecord.right_ascension,
                                  aliasMasterRecord.declination,
                                  separation)) \
            .where((MasterRecord.name < aliasMasterRecord.name) 
                      & (((timedelta(0) <= (MasterRecord.discover_date - aliasMasterRecord.discover_date))
                              & ((MasterRecord.discover_date - aliasMasterRecord.discover_date) < timedelta(1)))
                          | ((timedelta(0) <= (aliasMasterRecord.discover_date - MasterRecord.discover_date))
                              & ((aliasMasterRecord.discover_date - MasterRecord.discover_date) < timedelta(1)))
                        )
                  )

    cross_matches = session.execute(select_pairs).all()

    # Combine matches into disjoint sets of 1, 2, 3, 4, ...
    ds: DisjointSet[MasterRecord] = DisjointSet()
    for u, v in [row.tuple() for row in cross_matches]:
        ds.union(u, v)

    # Assign a representative member in each set and update the table
    # so that the other members point to it via the `alias_of` foreign key
    for s in cast(Iterator[set[MasterRecord]], ds.itersets()):
        unique_records = list(s)

        # TODO: the best records are the ones from TNS with the most information
        # (e.g. `claimed_type` not NULL). Use a cost function to evaluate each member
        # and choose the best as the representative.
        rep_idx = next((i for i, record in enumerate(unique_records) if record.source == Source.TNS), 0)
        for i, record in enumerate(unique_records):
            if i != rep_idx:
                record.alias_of = unique_records[rep_idx].id
    session.commit()
    
    select_reps = select(MasterRecord)\
                    .filter(MasterRecord.alias_of == None)\
                    .filter(MasterRecord.right_ascension != None)\
                    .filter(MasterRecord.declination != None)
    unique_records = [row.tuple()[0] for row in session.execute(select_reps).all()]

    session.add_all(
            CleanedRecord(master_id=record.id,
                          name=record.name,
                          right_ascension=unwrap(record.right_ascension),
                          declination=unwrap(record.declination),
                          discover_date=record.discover_date,
                          claimed_type=record.claimed_type,
                          source=record.source) for record in unique_records
    )
    session.commit()

    prepare_q3c_index(CLEANED_TABLE_NAME, session)
    session.commit()
