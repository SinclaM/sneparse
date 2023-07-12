#!/usr/bin/env python3
from typing import Optional
from pprint import pprint
from csv import DictReader
from dataclasses import dataclass
import os
from pathlib import Path
import re

from tqdm import tqdm
from aplpy.core import log
from sqlalchemy import URL, create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session

from sneparse import RESOURCES
from sneparse.util import unwrap
from sneparse.imaging import plot_image_astropy, plot_image_apl


EPOCH_RE = re.compile(r"(?<=VLASS).+(?=\.ql)")
VERSION_RE = re.compile(r"(?<=\.v).+(?=\.I\.iter)")

def find_paths(session: Session, file_name: str, epoch: int) -> set[Path]:
    like = re.sub(VERSION_RE, "%", re.sub(EPOCH_RE, f"{epoch}.%", file_name))

    select_path_name = text(f"SELECT path_to_file FROM file_definition WHERE file_name LIKE '{like}'")
    result = session.execute(select_path_name).all()

    return { Path("/projects/b1094/software/catalogs/").joinpath(row[0]) for row in result }

@dataclass
class CrossMatchInfo():
    file_paths: set[Path]
    ra: float
    dec: float
 
if __name__ == "__main__":
    engine = create_engine(URL.create(
        drivername=unwrap(os.getenv("DRIVER_NAME")),
        username  =os.getenv("VLASS_USERNAME"),
        password  =os.getenv("VLASS_PASSWORD"),
        host      =os.getenv("VLASS_HOST"),
        database  =os.getenv("VLASS_DATABASE"),
        port      =int(unwrap(os.getenv("VLASS_PORT")))
    ))

    session_maker = sessionmaker(engine)
    with session_maker() as session:
        fails: list[str] = []

        epoch = 1
        sne: dict[str, CrossMatchInfo] = {}

        # Total for tqdm to display. -2 for header and trailing newline (but it doesnt
        # have to be precise).
        total = sum(1 for _ in RESOURCES.joinpath("cross_matches.csv").open()) - 2;

        with RESOURCES.joinpath("cross_matches.csv").open() as f:
            for row in tqdm(DictReader(f), total=total):
                file_paths = find_paths(session, row["file_name"], epoch)

                if len(file_paths) == 0:
                    fails.append(row["file_name"])

                if row["name"] not in sne:
                    sne[row["name"]] = CrossMatchInfo(file_paths,
                                                      float(row["right_ascension"]),
                                                      float(row["declination"]))
                else:
                    sne[row["name"]].file_paths.update(file_paths)

        if len(fails) > 0:
            print(f"Unable to find FITS files for the following file names in epoch {epoch}:")
            pprint(fails)

        # Turn off aplpy logs
        # log.disabled = True

        # for (name, info) in sne.items():
            # file_paths = info.file_paths
            # ra = info.ra
            # dec = info.dec
            # print(file_paths)
            # try:
                # fig = plot_image_apl(ra, dec, name=name, cmap="gray_r", filters="r")
                # fig.save(RESOURCES.joinpath("images", "cross_matches", name))
                # fig.close()
                # print(f"[SUCCESS] Plotted source \"{name}\" (ra={ra}, dec={dec}).")
            # except Exception as e:
                # print(e)
                # print(f"[FAIL] Failed to plot source \"{name}\" (ra={ra}, dec={dec}).")
