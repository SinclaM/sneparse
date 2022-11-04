from __future__ import annotations # for postponed annotation evaluation
from typing import Optional, Any
from datetime import (datetime, timedelta)

from sneparse.coordinates import DecimalDegrees, DegreesMinutesSeconds, HoursMinutesSeconds

class SneRecord():
    """
    A record of a suspected supernova explosion (SNe).

    An `SneRecord` includes a `name` (e.g. 'ASASSN-20ao'), a `right_ascension` and
    `declination` in units of decimal degrees, a `claimed_type` (e.g. 'Candidate'),
    (TODO date), and a `source` (e.g.
    'https://github.com/astrocatalogs/sne-2020-2024/blob/main/ASASSN-20ao.json').

    """
    def __init__(self, name: str, ra: Optional[HoursMinutesSeconds], dec: Optional[DegreesMinutesSeconds],
                 discover_date: Optional[datetime], claimed_type: Optional[str], source: str) -> None:
        self.name            = name
        self.right_ascension = DecimalDegrees.from_hms(ra) if ra is not None else None
        self.declination     = DecimalDegrees.from_dms(dec) if dec is not None else None
        self.discover_date   = discover_date
        self.claimed_type    = claimed_type
        self.source          = source

    def __str__(self) -> str:
        return f"""SneRecord(name={self.name}, right_ascension={self.right_ascension}, \
declination={self.declination}, discover_date={self.discover_date}, claimed_type={self.claimed_type}, \
source={self.source})"""

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other: SneRecord) -> bool:
        return self.name == other.name \
                and self.right_ascension == other.right_ascension \
                and self.declination == other.declination \
                and self.claimed_type == other.claimed_type \
                and self.source == other.source

    @classmethod
    def from_oac(cls, oac_record: dict[str, Any]) -> SneRecord:
        # TODO: clean up the list indexing throughout this function
        oac_record = oac_record[list(oac_record.keys())[0]]
        name: str = oac_record["name"]

        ra: Optional[HoursMinutesSeconds]
        try:
            ra = HoursMinutesSeconds.from_str(oac_record["ra"][0]["value"])
        except KeyError:
            ra = None

        dec: Optional[DegreesMinutesSeconds]
        try:
            dec = DegreesMinutesSeconds.from_str(oac_record["dec"][0]["value"])
        except KeyError:
            dec = None

        discover_date: Optional[datetime]
        date_str: str
        try:
            date_str = oac_record["discoverdate"][0]["value"]
        except KeyError:
            discover_date = None
        else:
            discover_date = try_parse_date(date_str)

        claimed_type: Optional[str]
        try:
            claimed_type= oac_record["claimedtype"][0]["value"]
        except KeyError:
            claimed_type = None

        # TODO: consider having source be a URL passed as an argument
        #       to this function
        source = "OAC"
        return SneRecord(name, ra, dec, discover_date, claimed_type, source)

def try_parse_date(s: str):
    dt = timedelta(0)
    try:
        year, month, day = s.split("/")
        dt = timedelta(days=float(day) % 1)
        # TODO: there has to be a prettier way than str(int(float(...)))
        base = int(float(day))
        s = "/".join((year, month, str(base)))
    except ValueError:
        pass

    for fmt in ("%Y/%m/%d", "%Y/%m", "%Y"):
        try:
            return datetime.strptime(s, fmt) + dt
        except ValueError:
            pass
    raise Exception(f"Unable to parse date '{s}'")
