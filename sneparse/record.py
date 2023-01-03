from __future__ import annotations # for postponed annotation evaluation
from typing import Optional, Any, Iterator, Union
from datetime import (datetime, timedelta)
from enum import Enum
import csv

from sneparse.coordinates import DecimalDegrees, DegreesMinutesSeconds, HoursMinutesSeconds

ra_units  = Optional[Union[float, DecimalDegrees, HoursMinutesSeconds]]
dec_units = Optional[Union[float, DecimalDegrees, DegreesMinutesSeconds]]

# Order of inheritance is important here. See https://stackoverflow.com/a/58608362.
# With python 3.11 this could simply be a StrEnum.
class Source(str, Enum):
    OAC = "OAC"
    TNS = "TNS"

    @classmethod
    def from_str(cls, s: str) -> Source:
        match s:
            case 'Source.OAC':
                return Source.OAC
            case 'Source.TNS':
                return Source.TNS
            case _:
                raise Exception(f"Invalid source: {s}")
        


class SneRecord():
    """
    A record of a suspected supernova explosion (SNe).

    An `SneRecord` includes a `name` (e.g. 'ASASSN-20ao'), a `right_ascension` and
    `declination` in units of decimal degrees, a `claimed_type` (e.g. 'Candidate'),
    a `discover_date`, and a `source` (e.g. either from the Open Supernova Catalog
    or the Transient Name Server).

    """
    def __init__(self, name: str, ra: ra_units, dec: dec_units,
                 discover_date: Optional[datetime], claimed_type: Optional[str], source: Source) -> None:
        self.name            = name

        match ra:
            case float():
                self.right_ascension = DecimalDegrees(ra)
            case DecimalDegrees():
                self.right_ascension = ra
            case HoursMinutesSeconds():
                self.right_ascension = DecimalDegrees.from_hms(ra)
            case None:
                self.right_ascension = None
            case _:
                raise Exception("Invalid right ascension")

        match dec:
            case float():
                self.declination = DecimalDegrees(dec)
            case DecimalDegrees():
                self.declination = dec
            case DegreesMinutesSeconds():
                self.declination = DecimalDegrees.from_dms(dec)
            case None:
                self.declination = None
            case _:
                raise Exception("Invalid declination")

        self.discover_date   = discover_date
        self.claimed_type    = claimed_type
        self.source          = source

    def __str__(self) -> str:
        return f"""SneRecord(name={self.name}, right_ascension={self.right_ascension}, declination={self.declination}, discover_date={self.discover_date}, claimed_type={self.claimed_type}, source={self.source})"""

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other: SneRecord) -> bool:
        return self.name == other.name \
                and self.right_ascension == other.right_ascension \
                and self.declination == other.declination \
                and self.discover_date == other.discover_date \
                and self.claimed_type == other.claimed_type \
                and self.source == other.source

    def as_row(self) -> Iterator[str]:
        # TODO: rewrite this
        return (str(v) if not isinstance(v, datetime) else v.strftime("%Y-%m-%d %H:%M:%S.%f") for _, v in vars(self).items())

    @classmethod
    def from_oac(cls, oac_record: dict[str, Any]) -> SneRecord:
        """
        Create a `SneRecord` from a dictionary associated with an
        OAC Schema v1 document.
        """
        # TODO: clean up the list indexing throughout this function

        # Jump down one level, since the top-level dictionary
        # only has one key, value pair. The value is another
        # dictionary which contains all the information.
        oac_record = oac_record[list(oac_record.keys())[0]]

        # There will always be a name
        name: str = oac_record["name"]

        # Right ascension does not always exist
        ra: Optional[HoursMinutesSeconds]
        try:
            ra = HoursMinutesSeconds.from_str(oac_record["ra"][0]["value"])
        except KeyError:
            ra = None

        # Declination does not always exist
        dec: Optional[DegreesMinutesSeconds]
        try:
            dec = DegreesMinutesSeconds.from_str(oac_record["dec"][0]["value"])
        except KeyError:
            dec = None

        # Discovery date does not always exist
        discover_date: Optional[datetime]
        date_str: str
        try:
            date_str = oac_record["discoverdate"][0]["value"]
        except KeyError:
            discover_date = None
        else:
            discover_date = try_parse_date(date_str)

        # Claimed type does not always exist
        claimed_type: Optional[str]
        try:
            claimed_type= oac_record["claimedtype"][0]["value"]
        except KeyError:
            claimed_type = None

        source = Source.OAC
        return SneRecord(name, ra, dec, discover_date, claimed_type, source)

    @classmethod
    def from_tns(cls, reader: csv.DictReader) -> list[SneRecord]:
        """
        Create a list of `SneRecord`s from a TNS tsv file.
        """
        records: list[SneRecord] = []

        # Skip the first row, which is the header
        next(reader)

        for row in reader:
            # There will always be a name
            name: str = row["Name"]

            # Right ascension does not always exist
            ra: Optional[HoursMinutesSeconds]
            try:
                ra = HoursMinutesSeconds.from_str(row["RA"])
            except KeyError:
                ra = None

            # Declination does not always exist
            dec: Optional[DegreesMinutesSeconds]
            try:
                dec = DegreesMinutesSeconds.from_str(row["DEC"])
            except KeyError:
                dec = None

            # Discovery date does not always exist
            discover_date: Optional[datetime]
            date_str: str
            try:
                date_str = row["Discovery Date (UT)"]
            except KeyError:
                discover_date = None
            else:
                discover_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S.%f")

            # Claimed type does not always exist
            claimed_type: Optional[str]
            try:
                claimed_type= row["Obj. Type"]
            except KeyError:
                claimed_type = None

            source = Source.TNS
            records.append(SneRecord(name, ra, dec, discover_date, claimed_type, source))
        return records

def try_parse_date(s: str) -> datetime:
    """
    Try to get a datetime value out of a string, `s`.
    Note that OAC dates appear in multiple formats:
    `yyyy/mm/dd` (with the possibility of fractional days),
    `yyyy/mm`, or `yyyy`. This function will try to
    each one until it successful parses a date, or it will
    raise an exception.
    """
    # Some dates may be before 1000 AD. We need to pad them
    # with zeros on the left so that they are 4-digits and
    # parsable by datetime.
    #
    # But wait! There's at least one record--
    # and by at least one I mean exactly one ('SN1667A'
    # from the pre-1990 datatest) as far as I can tell--
    # where the date is stored as mm/dd/yyyy. Great.
    #
    # How can we even distinguish between yyyy/mm/dd and
    # mm/dd/yyyy then? Well, we can't--if the year is before
    # 32 AD. Otherwise, we can check if the first value is
    # greater than 31 and figure out the format from there.
    #
    # Hopefully there are no supernovae between 0 and 31 AD
    # recorded in the OAC catalog.
    #
    # Oh, and this of course means any dd/mm/yyyy style
    # dates with dd <= 12 are completely ambiguous with
    # the mm/dd/yyyy dates. Are there any such dates
    # in the OAC catalog? It's literally impossible to know
    # without reference another catalog.
    #
    # And by the way, we ignore the possibility of fractional
    # days for the few mm/dd/yyyy dates. It doesn't look
    # like there are any in the OAC catalog.
    #
    # Why can't everyone just agree on one format...
    split = s.split("/")
    if int(split[0]) > 31:
        split[0] = split[0].zfill(4)
    else:
        split[2] = split[2].zfill(4)

    # Now we need to handle dates with fractional days,
    # like '2022/11/11.52435'.
    dt = timedelta(0)
    try:
        # Try to split the string assuming it is yyyy/mm/dd.
        # This will fail if that's not the case, but that just
        # means we don't have to handle fractional days (since
        # no day is even reported).
        year, month, day = split

        # Get the fractional part of the day and turn it into a time span.
        # This will stay zero if the day is an integer. This time span
        # will be later added back to the datetime.
        dt = timedelta(days=float(day) % 1)

        # Recast the string to exclude the fractional part of the day.
        # TODO: there has to be a prettier way than str(int(float(...)))
        base = int(float(day))
        s = "/".join((year, month, str(base)))
    except ValueError:
        pass

    # Try each possible format.
    # Note that mm/dd/yyyy is tried last, to account for the
    # schema-noncompliant date(s) (I'm looking at you, 'SN1667A').
    for fmt in ("%Y/%m/%d", "%Y/%m", "%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt) + dt
        except ValueError:
            pass
    raise Exception(f"Unable to parse date '{s}'")
