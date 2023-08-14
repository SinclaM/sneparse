#!/usr/bin/env python3
from pathlib import Path
import argparse
import shutil
import os

from tqdm import tqdm
from sqlalchemy.sql.elements import TextClause
from sqlalchemy import URL, create_engine, select, text
from sqlalchemy.orm import sessionmaker

from sneparse.db.models import *
from sneparse.coordinates import DecimalDegrees, DegreesMinutesSeconds
from sneparse.util import unwrap

DEFAULT_CATEGORIES = [
    "agn",
    "bad",
    "bizarre_radio",
    "galactic",
    "good",
    "low_dec",
    "in_wise",
    "in_nvss_or_first",
    "nuclear",
    "pre_explosion",
    "unclear",
    "unsorted",
    "weak_radio"
]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("src", type=Path)
    parser.add_argument("dest", type=Path)

    args = parser.parse_args()
    src: Path = args.src
    dest: Path = args.dest

    for category in DEFAULT_CATEGORIES:
        dest.joinpath(category).mkdir(exist_ok=True)

    vlass_engine = create_engine(URL.create(
        drivername=unwrap(os.getenv("DRIVER_NAME")),
        username  =os.getenv("TRANSIENTS_USERNAME"),
        password  =os.getenv("TRANSIENTS_PASSWORD"),
        host      =os.getenv("TRANSIENTS_HOST"),
        database  ="vlass",
        port      =int(unwrap(os.getenv("TRANSIENTS_PORT")))
    ))

    vlass_session_maker = sessionmaker(vlass_engine)

    nvss_engine = create_engine(URL.create(
        drivername=unwrap(os.getenv("DRIVER_NAME")),
        username  =os.getenv("TRANSIENTS_USERNAME"),
        password  =os.getenv("TRANSIENTS_PASSWORD"),
        host      =os.getenv("TRANSIENTS_HOST"),
        database  ="nvss",
        port      =int(unwrap(os.getenv("TRANSIENTS_PORT")))
    ))

    nvss_session_maker = sessionmaker(nvss_engine)

    first_engine = create_engine(URL.create(
        drivername=unwrap(os.getenv("DRIVER_NAME")),
        username  =os.getenv("TRANSIENTS_USERNAME"),
        password  =os.getenv("TRANSIENTS_PASSWORD"),
        host      =os.getenv("TRANSIENTS_HOST"),
        database  ="first",
        port      =int(unwrap(os.getenv("TRANSIENTS_PORT")))
    ))

    first_session_maker = sessionmaker(first_engine)

    wise_engine = create_engine(URL.create(
        drivername=unwrap(os.getenv("DRIVER_NAME")),
        username  =os.getenv("TRANSIENTS_USERNAME"),
        password  =os.getenv("TRANSIENTS_PASSWORD"),
        host      =os.getenv("TRANSIENTS_HOST"),
        database  ="wise",
        port      =int(unwrap(os.getenv("TRANSIENTS_PORT")))
    ))

    wise_session_maker = sessionmaker(wise_engine)

    with (
        vlass_session_maker() as vlass_session,
        nvss_session_maker() as nvss_session,
        first_session_maker() as first_session,
        wise_session_maker() as wise_session,
    ):
        total = sum(1 for _ in src.glob("*.png"))
        for file in tqdm(src.glob("*.png"), total=total):
            record = unwrap(
                vlass_session.execute(select(CleanedRecord).filter(CleanedRecord.name == file.stem)).first()
            )._tuple()[0]

            _5_arcseconds = DecimalDegrees.from_dms(DegreesMinutesSeconds(1, 0, 0, 5.0))
            _3point3_arcseconds = DecimalDegrees.from_dms(DegreesMinutesSeconds(1, 0, 0, 3.3))

            def cone_search(table: str, radius: DecimalDegrees) -> TextClause:
                radial_query_args = f"ra, decl, {record.right_ascension}, {record.declination}, {radius}"
                return text(f"SELECT * FROM {table} WHERE q3c_radial_query({radial_query_args});")

            if record.claimed_type is not None:
                shutil.copy(file, dest.joinpath("unsorted"))
            elif len(nvss_session.execute(cone_search("source", _5_arcseconds)).all()) > 0:
                shutil.copy(file, dest.joinpath("in_nvss_or_first"))
            elif len(first_session.execute(cone_search("source", _5_arcseconds)).all()) > 0:
                shutil.copy(file, dest.joinpath("in_nvss_or_first"))
            elif len(wise_session.execute(cone_search("assef_seventyfive", _3point3_arcseconds)).all()) > 0:
                shutil.copy(file, dest.joinpath("in_wise"))
            else:
                shutil.copy(file, dest.joinpath("unsorted"))
