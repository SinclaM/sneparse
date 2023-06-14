#!/usr/bin/env python3

from __future__ import annotations
import csv
import os
from io import StringIO

from sqlalchemy import URL, create_engine, text
from sqlalchemy.orm import sessionmaker

from sneparse.definitions import ROOT_DIR
from sneparse.db.models import CLEANED_TABLE_NAME
from sneparse.util import unwrap

if __name__ == "__main__":
    # Setup a connection to db with our catalog
    local_engine = create_engine(URL.create(
        drivername=unwrap(os.getenv("DRIVER_NAME")),
        username  =os.getenv("ASTRO_USERNAME"),
        password  =os.getenv("ASTRO_PASSWORD"),
        host      =os.getenv("ASTRO_HOST"),
        database  =os.getenv("ASTRO_DATABASE")
    ))

    catalog_buffer = StringIO()

    local_session_maker = sessionmaker(local_engine)  
    with local_session_maker() as session:
        # Copy local catalog to memory
        copy_to = f"COPY {CLEANED_TABLE_NAME} TO STDOUT WITH (FORMAT csv)"
        print(copy_to)
        session.connection().connection.cursor().copy_expert(copy_to, catalog_buffer)

    catalog_buffer.seek(0)

    # Setup a connection to CIERA's VLASS db.
    remote_engine = create_engine(URL.create(
        drivername=unwrap(os.getenv("DRIVER_NAME")),
        username  =os.getenv("VLASS_USERNAME"),
        password  =os.getenv("VLASS_PASSWORD"),
        host      =os.getenv("VLASS_HOST"),
        database  =os.getenv("VLASS_DATABASE"),
        port      =int(unwrap(os.getenv("VLASS_PORT")))
    ))

    remote_session_maker = sessionmaker(remote_engine)  
    with remote_session_maker() as session:
        # Create a temporary table to hold our catalog, and fill it with the
        # table we previously put in memory.
        #
        # Ideally, we could use posgres_fdw for this, but it is far too slow.
        temp_catalog = "temp_catalog"
        create_temp_catalog = text(
            f"""CREATE TEMPORARY TABLE {temp_catalog} (
                cleaned_id integer NOT NULL,
                master_id integer NOT NULL,
                name character varying NOT NULL,
                right_ascension double precision,
                declination double precision,
                discover_date timestamp without time zone,
                claimed_type character varying,
                source text NOT NULL
            );"""
        )
        print(create_temp_catalog)
        session.execute(create_temp_catalog)

        copy_from = f"COPY {temp_catalog} FROM STDIN WITH (FORMAT csv)"
        print(copy_from)
        session.connection().connection.cursor().copy_expert(copy_from, catalog_buffer)

        # Prepare the temp catalog table for cross matching
        q3c_prepare_catalog = text(
            f"""CREATE INDEX ON {temp_catalog} (q3c_ang2ipix("right_ascension", "declination"));
                CLUSTER {temp_catalog}_q3c_ang2ipix_idx ON {temp_catalog};
                ANALYZE {temp_catalog};"""
        )
        print(q3c_prepare_catalog)
        session.execute(q3c_prepare_catalog);

        # The foreign VLASS sources table is not indexed properly, so we create a temp
        # copy of it and prepare it for cross matching.
        temp_gaussian = "temp_gaussian"
        create_temp_gaussian = text(f"CREATE TEMPORARY TABLE {temp_gaussian} AS TABLE pybdsf_gaussian_epoch1")
        print(create_temp_gaussian)
        session.execute(create_temp_gaussian)

        q3c_prepare_gaussian = text(
            f"""CREATE INDEX ON {temp_gaussian} (q3c_ang2ipix("ra", "decl"));
                CLUSTER {temp_gaussian}_q3c_ang2ipix_idx ON {temp_gaussian};
                ANALYZE {temp_gaussian};"""
        )
        print(q3c_prepare_gaussian)
        session.execute(q3c_prepare_gaussian);

        # Do the actual cross matching.
        cross_match = text(
            f"""SELECT * FROM {temp_catalog} AS a, {temp_gaussian} AS b 
                where q3c_join(a.right_ascension, a.declination, b.ra, b.decl, 0.000555556)"""
        )
        print(cross_match)
        matches = session.execute(cross_match).all()

    output_file = ROOT_DIR.joinpath("resources", "cross_matches.csv")
    print(f"\nWriting results to {output_file}")
    with open(output_file, "w") as csvfile:
        # Save the results to an output file.
        writer = csv.writer(csvfile, delimiter=',')
        for match_ in matches:
            writer.writerow(match_.tuple())
