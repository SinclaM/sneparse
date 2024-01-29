#!/usr/bin/env python3
from typing import Optional
from collections import defaultdict
import os
from pathlib import Path
from csv import DictReader
from datetime import datetime
from dataclasses import dataclass
import argparse

from tqdm import tqdm
from aplpy.core import log
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker
import matplotlib.pyplot as plt

from sneparse import RESOURCES
from sneparse.record import SneRecord, Source
from sneparse.util import unwrap, find_paths
from sneparse.imaging import plot_image_apl

@dataclass
class OpticalSubplot: ...

@dataclass
class RadioSubplot:
    epoch: int

def subplot_relative_coordinates(subplot_type: OpticalSubplot | RadioSubplot, stacked: bool = True) -> list[float]:
    if stacked:
        span = 0.4
        margin = (0.5 - span) / 2.0
        match subplot_type:
            case OpticalSubplot():
                return [margin, 0.5 + margin, span, span]
            case RadioSubplot(epoch) if epoch == 1:
                return [margin, margin, span, span]
            case RadioSubplot(epoch) if epoch == 2:
                return [0.5 + margin, margin, span, span]
            case RadioSubplot(epoch) if epoch == 3:
                return [0.5 + margin, 0.5 + margin, span, span]
            case _:
                assert False
    else:
        x_margin = 0.07 * 2 / image_count
        x_span = (1 - x_margin - image_count * x_margin) / image_count

        match subplot_type:
            case OpticalSubplot():
                return [x_margin, 0.05, x_span, 0.9]
            case RadioSubplot(epoch):
                return [x_margin + epoch * (x_span + x_margin), 0.05, x_span, 0.9]

@dataclass
class Info:
    record: SneRecord
    vlass_fits_paths: list[Optional[Path]]

if __name__ == "__main__":
    EPOCH_START = 1
    EPOCH_END = 3 # inclusive
    NUM_EPOCHS = 1 + EPOCH_END - EPOCH_START

    parser = argparse.ArgumentParser()
    parser.add_argument("--sne", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--tde", action=argparse.BooleanOptionalAction, default=False)

    args = parser.parse_args()

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
    epoch_appearances: dict[str, list[int]] = defaultdict(list)

    sources_tde: dict[str, Optional[Info]] = {}
    epoch_appearances_tde: dict[str, list[int]] = defaultdict(list)

    if args.sne:
        for path in RESOURCES.joinpath("images").glob("epoch1_categorized/good/*.png"):
            good_sources[path.stem] = None
            epoch_appearances[path.stem].append(1)
        for path in RESOURCES.joinpath("images").glob("epoch2_categorized/good/*.png"):
            good_sources[path.stem] = None
            epoch_appearances[path.stem].append(2)
        for path in RESOURCES.joinpath("images").glob("epoch3_categorized/good/*.png"):
            good_sources[path.stem] = None
            epoch_appearances[path.stem].append(3)
    if args.tde:
        for path in RESOURCES.joinpath("images").glob("epoch1_cross_matches_tde/*.png"):
            sources_tde[path.stem] = None
            epoch_appearances_tde[path.stem].append(1)
        for path in RESOURCES.joinpath("images").glob("epoch2_cross_matches_tde/*.png"):
            sources_tde[path.stem] = None
            epoch_appearances_tde[path.stem].append(2)
        for path in RESOURCES.joinpath("images").glob("epoch3_cross_matches_tde/*.png"):
            sources_tde[path.stem] = None
            epoch_appearances_tde[path.stem].append(3)

    with session_maker() as session:
        for epoch in range(EPOCH_START, EPOCH_END + 1):
            if args.sne:
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

                            file_paths = [
                                next(iter(find_paths(session, row["file_name"], epoch)), None) for epoch in range(EPOCH_START, EPOCH_END + 1)
                            ] 

                            good_sources[record.name] = Info(record, file_paths)
            if args.tde:
                with RESOURCES.joinpath(f"epoch{epoch}_cross_matches_tde.csv").open() as f:
                    for row in DictReader(f):
                        if row["name"] in sources_tde and sources_tde[row["name"]] is None:
                            record = SneRecord(
                                row["name"],
                                float(row["right_ascension"]),
                                float(row["declination"]),
                                None if row["discover_date"] == "" else datetime.fromisoformat(row["discover_date"]),
                                None if row["claimed_type"] == "" else row["claimed_type"],
                                Source.OAC
                            )

                            file_paths = [
                                next(iter(find_paths(session, row["file_name"], epoch)), None) for epoch in range(EPOCH_START, EPOCH_END + 1)
                            ] 

                            sources_tde[record.name] = Info(record, file_paths)

    # Turn off aplpy logs
    log.disabled = True

    if args.sne:
        dest = RESOURCES.joinpath("images", "epoch_comparisons")
        dest.mkdir(exist_ok=True)

        for info in tqdm(good_sources.values()): 
            info = unwrap(info)
            record = info.record
            file_paths = info.vlass_fits_paths

            image_count = 1 + NUM_EPOCHS # 1 optical + radio epochs
            fig = plt.figure(figsize=(16, 16))

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
                subplot=subplot_relative_coordinates(OpticalSubplot())
            )

            for epoch in range(EPOCH_START, EPOCH_END + 1):
                if info.vlass_fits_paths[epoch - 1] is not None:
                    plot_image_apl(
                        record,
                        cmap="gray_r",
                        size=340,
                        image_file=str(info.vlass_fits_paths[epoch - 1]),
                        is_radio=True,
                        figure=fig,
                        subplot=subplot_relative_coordinates(RadioSubplot(epoch)),
                        is_non_detection=(epoch not in epoch_appearances[record.name])
                    )

            plt.savefig(dest.joinpath(f"{record.name}.png"))
            plt.close()

    if args.tde:
        dest = RESOURCES.joinpath("images", "epoch_comparisons_tde")
        dest.mkdir(exist_ok=True)

        for info in tqdm(sources_tde.values()): 
            info = unwrap(info)
            record = info.record
            file_paths = info.vlass_fits_paths

            image_count = 1 + NUM_EPOCHS # 1 optical + radio epochs
            fig = plt.figure(figsize=(16, 16))

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
                subplot=subplot_relative_coordinates(OpticalSubplot())
            )

            for epoch in range(EPOCH_START, EPOCH_END + 1):
                if info.vlass_fits_paths[epoch - 1] is not None:
                    plot_image_apl(
                        record,
                        cmap="gray_r",
                        size=340,
                        image_file=str(info.vlass_fits_paths[epoch - 1]),
                        is_radio=True,
                        figure=fig,
                        subplot=subplot_relative_coordinates(RadioSubplot(epoch)),
                        is_non_detection=(epoch not in epoch_appearances_tde[record.name])
                    )

            plt.savefig(dest.joinpath(f"{record.name}.png"))
            plt.close()
