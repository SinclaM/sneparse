#!/usr/bin/env python3
import argparse
from csv import DictReader
from datetime import datetime

from sneparse import RESOURCES
from sneparse.record import SneRecord

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--initial", nargs="+", help="<Required> Initial Epoch(s)", required=True)
    parser.add_argument("-f", "--final", nargs="+", help="<Required> Final Epoch(s)", required=True)

    args = parser.parse_args()
    initial_epochs: set[int] = set(args.initial)
    final_epochs: set[int] = set(args.final)
    assert len(initial_epochs & final_epochs) == 0

    initial_sources: set[SneRecord] = set()
    final_sources: set[SneRecord] = set()

    for epoch in initial_epochs:
        with RESOURCES.joinpath(f"epoch{epoch}_cross_matches.csv").open() as f:
            for row in DictReader(f):
                record = SneRecord(
                    row["name"],
                    float(row["right_ascension"]),
                    float(row["declination"]),
                    None if row["discover_date"] == "" else datetime.fromisoformat(row["discover_date"]),
                    None if row["claimed_type"] == "" else row["claimed_type"],
                    row["source"]
                )
                initial_sources.add(record)

    for epoch in final_epochs:
        with RESOURCES.joinpath(f"epoch{epoch}_cross_matches.csv").open() as f:
            for row in DictReader(f):
                record = SneRecord(
                    row["name"],
                    float(row["right_ascension"]),
                    float(row["declination"]),
                    None if row["discover_date"] == "" else datetime.fromisoformat(row["discover_date"]),
                    None if row["claimed_type"] == "" else row["claimed_type"],
                    row["source"]
                )
                final_sources.add(record)

    records = sorted((r for r in final_sources if r not in initial_sources), key=lambda r: r.discover_date)
    for r in records:
        color = bcolors.OKGREEN
        if r.claimed_type is None or r.claimed_type.upper() in ("REMOVED", "UNKNOWN"):
            color = bcolors.FAIL
        elif r.claimed_type.upper() == "CANDIDATE":
            color = bcolors.WARNING

        print(f"{r.name} | {color}{r.claimed_type}{bcolors.ENDC}")

