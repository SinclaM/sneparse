from __future__ import annotations # for postponed annotation evaluation
from sneparse.coordinates import DecimalDegrees, DegreesMinutesSeconds, HoursMinutesSeconds
import json

class SneRecord():
    """
    A record of a suspected supernova explosion (SNe).

    An `SneRecord` includes a `name` (e.g. 'ASASSN-20ao'), a `right_ascension` and 
    `declination` in units of decimal degrees, a `claimed_type` (e.g. 'Candidate'),
    (TODO date), and a `source` (e.g. 
    'https://github.com/astrocatalogs/sne-2020-2024/blob/main/ASASSN-20ao.json').

    """
    def __init__(self, name: str, ra: HoursMinutesSeconds, dec: DegreesMinutesSeconds, 
                 claimed_type: str, source: str) -> None:
        self.name            = name
        self.right_ascension = DecimalDegrees.from_hms(ra)
        self.declination     = DecimalDegrees.from_dms(dec)
        # TODO: add date
        self.claimed_type    = claimed_type
        self.source          = source

    def __str__(self) -> str:
        return f"""SneRecord(name={self.name}, right_ascension={self.right_ascension}, \
declination={self.declination}, claimed_type={self.claimed_type}, \
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
    def from_oac(cls, oac_json_record: str) -> SneRecord:
        d = json.loads(oac_json_record)

        # TODO: clean up the list indexing here
        d = d[list(d.keys())[0]]
        name: str = d["name"]
        ra  = HoursMinutesSeconds.from_str(d["ra"][0]["value"])
        dec = DegreesMinutesSeconds.from_str(d["dec"][0]["value"])
        claimed_type = d["claimedtype"][0]["value"]

        # TODO: consider having source be a URL passed as an argument 
        #       to this function
        source = "OAC"
        return SneRecord(name, ra, dec, claimed_type, source)
