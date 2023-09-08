#!/usr/bin/env python3
from typing import Optional
import os
from pathlib import Path
import re
from csv import DictReader
from datetime import datetime
from dataclasses import dataclass

from tqdm import tqdm
from aplpy.core import log
from sqlalchemy import URL, create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session
import matplotlib.pyplot as plt

from sneparse import RESOURCES
from sneparse.record import SneRecord, Source
from sneparse.util import unwrap
from sneparse.imaging import plot_image_apl

EPOCH_RE = re.compile(r"(?<=VLASS).+(?=\.ql)")
VERSION_RE = re.compile(r"(?<=\.v).+(?=\.I\.iter)")

def find_paths(session: Session, file_name: str, epoch: int) -> set[Path]:
    like = re.sub(VERSION_RE, "%", re.sub(EPOCH_RE, f"{epoch}.%", file_name))

    select_path_name = text(
        f"SELECT concat(path_to_file, file_name) FROM file_definition WHERE file_name LIKE '{like}';"
    )
    result = session.execute(select_path_name).all()

    return { Path("/projects/b1094/software/catalogs/").joinpath(row[0]) for row in result }

@dataclass
class Info:
    record: SneRecord
    vlass_fits_paths: list[Path]

if __name__ == "__main__":
    EPOCH_START = 1
    EPOCH_END = 2 # inclusive
    NUM_EPOCHS = 1 + EPOCH_END - EPOCH_START

    engine = create_engine(URL.create(
        drivername=unwrap(os.getenv("DRIVER_NAME")),
        username  =os.getenv("TRANSIENTS_USERNAME"),
        password  =os.getenv("TRANSIENTS_PASSWORD"),
        host      =os.getenv("TRANSIENTS_HOST"),
        database  ="vlass",
        port      =int(unwrap(os.getenv("TRANSIENTS_PORT")))
    ))

    session_maker = sessionmaker(engine)

    good_sources: dict[str, Optional[Info]] = {}

    for path in RESOURCES.joinpath("images").glob(f"epoch*_categorized/good/*.png"):
        good_sources[path.stem] = None

    with session_maker() as session:
        for epoch in range(EPOCH_START, EPOCH_END + 1):
            with RESOURCES.joinpath(f"epoch{epoch}_cross_matches.csv").open("r") as f:
                for row in DictReader(f):
                    if row["name"] in good_sources and good_sources[row["name"]] is None:
                        record = SneRecord(
                            row["name"],
                            float(row["right_ascension"]),
                            float(row["declination"]),
                            None if row["discover_date"] == "" else datetime.fromisoformat(row["discover_date"]),
                            None if row["claimed_type"] == "" else row["claimed_type"],
                            Source(row["source"])
                        )

                        file_paths = [list(find_paths(session, row["file_name"], epoch))[0] for epoch in range(EPOCH_START, EPOCH_END + 1)] 
                        good_sources[record.name] = Info(record, file_paths)

    # Turn off aplpy logs
    log.disabled = True

    dest = RESOURCES.joinpath("images", "epoch_comparisons")
    dest.mkdir(exist_ok=True)

    for info in tqdm(good_sources.values()): 
        info = unwrap(info)
        record = info.record
        file_paths = info.vlass_fits_paths

        image_count = 1 + NUM_EPOCHS # 1 optical + radio epochs
        fig = plt.figure(figsize=(8 * image_count, 8))

        title_date = "Unknown discovery date" if record.discover_date is None \
                        else f"Discovered {record.discover_date.date()}"

        title_claimed_type = "Unknown claimed type" if record.claimed_type is None \
                        else f"Type {record.claimed_type}"

        fig.suptitle( f"{record.name}        {title_date}        {title_claimed_type}", size="xx-large")

        x_margin = 0.07 * 2 / image_count
        x_span = (1 - x_margin - image_count * x_margin) / image_count

        plot_image_apl(
            record,
            cmap="gray_r",
            size=340,
            filters="r",
            is_radio=False,
            figure=fig,
            subplot=[x_margin, 0.05, x_span, 0.9]
        )

        for epoch in range(EPOCH_START, EPOCH_END + 1):
            plot_image_apl(
                record,
                cmap="gray_r",
                size=340,
                image_file=str(info.vlass_fits_paths[epoch - 1]),
                is_radio=True,
                figure=fig,
                subplot=[x_margin + epoch * (x_span + x_margin), 0.05, x_span, 0.9]
            )

        plt.savefig(dest.joinpath(f"{record.name}.png"))
        plt.close()
