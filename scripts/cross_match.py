#!/usr/bin/env python3

from __future__ import annotations
import os
from io import StringIO
import argparse

from sqlalchemy import URL, create_engine, text
from sqlalchemy.orm import sessionmaker

from sneparse import RESOURCES
from sneparse.coordinates import DecimalDegrees, DegreesMinutesSeconds
from sneparse.db.models import CLEANED_TABLE_NAME, TDE_TABLE_NAME
from sneparse.util import unwrap

EPOCH_DATE_CUTOFFS = {
    1: "2020-01-01",
    2: "2022-03-01",
    3: "2024-01-01",
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sne", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--tde", action=argparse.BooleanOptionalAction, default=False)
    args = parser.parse_args()

    epoch = int(unwrap(os.getenv("EPOCH")))

    separation = DecimalDegrees.from_dms(DegreesMinutesSeconds(1, 0, 0, 5)).degrees

    # Setup a connection to CIERA's VLASS db.
    engine = create_engine(URL.create(
        drivername=unwrap(os.getenv("DRIVER_NAME")),
        username  =os.getenv("TRANSIENTS_USERNAME"),
        password  =os.getenv("TRANSIENTS_PASSWORD"),
        host      =os.getenv("TRANSIENTS_HOST"),
        database  ="vlass",
        port      =int(unwrap(os.getenv("TRANSIENTS_PORT")))
    ))

    session_maker = sessionmaker(engine)  

    if args.sne:
        with session_maker() as session:
            gaussian = "pybdsf_gaussian"

            temp_cross_match = "temp_cross_match"
            cross_match = text(
                f"CREATE TEMPORARY TABLE {temp_cross_match} AS                                    \n"
                f"    SELECT * FROM {CLEANED_TABLE_NAME} AS a, {gaussian} AS b                    \n"
                f"    WHERE q3c_join(a.right_ascension, a.declination, b.ra, b.decl, {separation})\n"
                f"        AND b.file_name LIKE 'VLASS{epoch}%'                                    \n"
                f"        AND a.discover_date < TIMESTAMP '{EPOCH_DATE_CUTOFFS[epoch]}';          \n"
            )
            print(cross_match)
            session.execute(cross_match)

            # Copy cross matches into memory
            cross_matches_buffer = StringIO()
            copy_cross_matches = f"COPY {temp_cross_match} TO STDOUT WITH (FORMAT csv, HEADER);\n"
            print(copy_cross_matches)
            session.connection().connection.cursor().copy_expert(copy_cross_matches, cross_matches_buffer)
            cross_matches_buffer.seek(0)

        output_file = RESOURCES.joinpath(f"epoch{epoch}_cross_matches.csv")
        print(f"Writing results to {output_file}")
        with open(output_file, "w") as csvfile:
            # Save the results to an output file.
            print(cross_matches_buffer.getvalue(), file=csvfile)
    if args.tde:
        with session_maker() as session:
            gaussian = "pybdsf_gaussian"

            temp_cross_match = "temp_cross_match_tde"
            cross_match = text(
                f"CREATE TEMPORARY TABLE {temp_cross_match} AS                                    \n"
                f"    SELECT * FROM {TDE_TABLE_NAME} AS a, {gaussian} AS b                        \n"
                f"    WHERE q3c_join(a.right_ascension, a.declination, b.ra, b.decl, {separation})\n"
                f"        AND b.file_name LIKE 'VLASS{epoch}%'                                    \n"
                f"        AND a.discover_date < TIMESTAMP '{EPOCH_DATE_CUTOFFS[epoch]}'           \n"
            )
            print(cross_match)
            session.execute(cross_match)

            # Copy cross matches into memory
            cross_matches_buffer = StringIO()
            copy_cross_matches = f"COPY {temp_cross_match} TO STDOUT WITH (FORMAT csv, HEADER);\n"
            print(copy_cross_matches)
            session.connection().connection.cursor().copy_expert(copy_cross_matches, cross_matches_buffer)
            cross_matches_buffer.seek(0)

        output_file = RESOURCES.joinpath(f"epoch{epoch}_cross_matches_tde.csv")
        print(f"Writing results to {output_file}")
        with open(output_file, "w") as csvfile:
            # Save the results to an output file.
            print(cross_matches_buffer.getvalue(), file=csvfile)

