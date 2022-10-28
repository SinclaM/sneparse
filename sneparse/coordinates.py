from __future__ import annotations # for postponed annotation evaluation
from typing import Literal
from math import floor

HMS_HOURS_PER_DEGREE = 24.0 / 360.0
HMS_MINUTES_PER_HOUR = 60
HMS_SECONDS_PER_MINUTE = 60

DMS_MINUTES_PER_DEGREE = 60
DMS_SECONDS_PER_MINUTE = 60

FLOAT_EPSILON = 1e-6

class HoursMinutesSeconds():
    """
The unit of right ascension. Angles are broken into `hours` (0-24), `minutes` (0-59),\
 and `seconds` (0.0 - 59.999...). An angle in hours:minutes:seconds also has an associated\
 `sign` (+ or -).
    """
    def __init__(self, sign: Literal[-1, 1], hours: int, minutes: int, seconds: float) -> None:
        self.sign    = sign
        self.hours   = hours
        self.minutes = minutes
        self.seconds = seconds

    def __str__(self) -> str:
        return f"{'+' if self.sign == 1 else '-'}{self.hours:02}:{self.minutes:02}:{self.seconds}"

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other: HoursMinutesSeconds) -> bool:
        # Note the fuzzy equality for the floating point value
        return self.sign == other.sign \
                and self.hours == other.hours \
                and self.minutes == other.minutes \
                and abs(self.seconds - other.seconds) < FLOAT_EPSILON

    @classmethod
    def from_decimal_degrees(cls, d: DecimalDegrees) -> HoursMinutesSeconds:
        """
        Converts a `DecimalDegrees` value to `HoursMinutesSeconds`.
        """
        deg = d.degrees
        while deg > 360.0:
            deg -= 360.0

        hours   = floor(HMS_HOURS_PER_DEGREE * deg)
        deg -= hours / HMS_HOURS_PER_DEGREE
        minutes = floor(HMS_HOURS_PER_DEGREE * HMS_MINUTES_PER_HOUR * deg)
        deg -= minutes / (HMS_HOURS_PER_DEGREE * HMS_MINUTES_PER_HOUR)
        seconds = HMS_HOURS_PER_DEGREE * HMS_MINUTES_PER_HOUR * HMS_SECONDS_PER_MINUTE * deg

        return HoursMinutesSeconds(1, hours, minutes, seconds)

    @classmethod
    def from_str(cls, s: str) -> HoursMinutesSeconds:
        try:
            first, second, third = s.split(":")

            # if the + or - is excluded, the sign is positive
            if len(first) == 2:
                sign = 1
            # otherwise get the sign from the first character
            else:
                sign = first[0]
                first = first[1:]
                if sign == "+":
                    sign = 1
                elif sign == "-":
                    sign = -1
                else:
                    raise Exception

            hh = int(first)
            mm = int(second)
            ss = float(third)
        except:
            raise Exception(f"Unable to parse {s} into HoursMinutesSeconds object")

        return HoursMinutesSeconds(sign, hh, mm, ss)

class DecimalDegrees():
    """
A base 10 representation of angles, in degrees.
    """
    def __init__(self, degrees: float) -> None:
        self.degrees = degrees

    def __str__(self) -> str:
        return f"{self.degrees}°"

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other: DecimalDegrees) -> bool:
        # Note the fuzzy equality for the floating point value
        return abs(self.degrees - other.degrees) < 1e-6

    @classmethod
    def from_hms(cls, hms: HoursMinutesSeconds) -> DecimalDegrees:
        """
        Converts an `HoursMinutesSeconds` value to `DecimalDegrees`.
        """
        return DecimalDegrees(hms.sign * (
            hms.hours / HMS_HOURS_PER_DEGREE
            + hms.minutes / (HMS_HOURS_PER_DEGREE * HMS_MINUTES_PER_HOUR)
            + hms.seconds / (HMS_HOURS_PER_DEGREE * HMS_MINUTES_PER_HOUR * HMS_SECONDS_PER_MINUTE)))

    @classmethod
    def from_dms(cls, dms: DegreesMinutesSeconds) -> DecimalDegrees:
        """
        Converts a `DegreesMinutesSeconds` value to `DecimalDegrees`.
        """
        return DecimalDegrees(dms.sign * (
            dms.degrees
            + dms.minutes / DMS_MINUTES_PER_DEGREE
            + dms.seconds / (DMS_MINUTES_PER_DEGREE * HMS_SECONDS_PER_MINUTE)))

class DegreesMinutesSeconds():
    """
The unit of declination. Angles are broken into `degrees` (0-359), `minutes` (0-59),\
 and `seconds` (0.0 - 59.999...). An angle in degrees:minutes:seconds also has an associated\
 `sign` (+ or -).
    """
    def __init__(self, sign: Literal[-1, 1], degrees: int, minutes: int, seconds: float) -> None:
        self.sign    = sign
        self.degrees = degrees
        self.minutes = minutes
        self.seconds = seconds

    def __str__(self) -> str:
        return f"{'+' if self.sign == 1 else '-'}{self.degrees:02}:{self.minutes:02}:{self.seconds}"

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other: DegreesMinutesSeconds) -> bool:
        # Note the fuzzy equality for the floating point value
        return self.sign == other.sign \
                and self.degrees == other.degrees \
                and self.minutes == other.minutes \
                and abs(self.seconds - other.seconds) < FLOAT_EPSILON

    @classmethod
    def from_decimal_degrees(cls, d: DecimalDegrees) -> DegreesMinutesSeconds:
        """
        Converts a `DecimalDegrees` value to `DegreesMinutesSeconds`.
        """
        deg = d.degrees
        while deg > 360.0:
            deg -= 360.0

        degrees   = floor(deg)
        deg -= degrees
        minutes = floor(DMS_MINUTES_PER_DEGREE * deg)
        deg -= minutes / DMS_MINUTES_PER_DEGREE
        seconds = DMS_MINUTES_PER_DEGREE * DMS_SECONDS_PER_MINUTE * deg

        return DegreesMinutesSeconds(1, degrees, minutes, seconds)

    @classmethod
    def from_str(cls, s: str) -> DegreesMinutesSeconds:
        try:
            first, second, third = s.split(":")
            
            sign = first[0]
            if sign == "+":
                sign = 1
            elif sign == "-":
                sign = -1
            else:
                raise Exception

            dd = int(first[1:])
            mm = int(second)
            ss = float(third)
        except:
            raise Exception(f"Unable to parse {s} into DegreesMinutesSeconds object")

        return DegreesMinutesSeconds(sign, dd, mm, ss)
