from __future__ import annotations # for postponed annotation evaluation
from typing import Literal, Tuple, Optional
from math import (floor, sin, cos, acos, radians, degrees)

HMS_HOURS_PER_DEGREE = 24.0 / 360.0
HMS_MINUTES_PER_HOUR = 60
HMS_SECONDS_PER_MINUTE = 60

DMS_MINUTES_PER_DEGREE = 60
DMS_SECONDS_PER_MINUTE = 60

FLOAT_EPSILON = 1e-6

class HoursMinutesSeconds():
    """
    The unit of right ascension.

    Angles are broken into `hours` (0-24), `minutes` (0-59), and
    `seconds` (0.0 - 59.999...). An angle in hours:minutes:seconds 
    also has an associated `sign` (+ or -).
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
        return HoursMinutesSeconds(*parse_sexagesimal(s))

class DecimalDegrees():
    """
    A base 10 representation of angles, in degrees.
    """
    def __init__(self, degrees: float) -> None:
        self.degrees = degrees

    def __str__(self) -> str:
        return str(self.degrees)

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
    The unit of declination.

    Angles are broken into `degrees` (0-359), `minutes` (0-59), and
    `seconds` (0.0 - 59.999...). An angle in degrees:minutes:seconds
    also has an associated `sign` (+ or -).
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
        return DegreesMinutesSeconds(*parse_sexagesimal(s))

def parse_sexagesimal(s: str) -> Tuple[Literal[1, -1], int, int, float]:
    split = s.split(":")
    hh: int
    mm: int
    ss: float
    if len(split) == 3:
        first, second, third = split

        # if the + or - is excluded, the sign is positive
        if first[0].isdigit():
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
                raise Exception(f"Unable to parse {s} into HoursMinutesSeconds object")

        hh = int(first)
        mm = int(second)
        ss = float(third)
    elif len(split) == 2:
        first, second = split

        # if the + or - is excluded, the sign is positive
        if first[0].isdigit():
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
                raise Exception(f"Unable to parse {s} into HoursMinutesSeconds object")

        hh = 0
        mm = int(first)
        ss = float(second)
    elif len(split) == 1:
        first = split[0]
        # if the + or - is excluded, the sign is positive
        if first[0].isdigit():
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
                raise Exception(f"Unable to parse {s} into HoursMinutesSeconds object")
        hh = 0
        mm = 0
        ss = float(first)

    else:
        raise Exception(f"Unable to parse {s} into HoursMinutesSeconds object")

    return (sign, hh, mm, ss)

def angular_separation(ra1: DecimalDegrees, d1: DecimalDegrees, ra2: DecimalDegrees, d2: DecimalDegrees) \
        -> DecimalDegrees:
    """
    Calculates the angular separation, in degrees, between the `(ra1, d1)` and `(ra2, d2)`.
    """
    return DecimalDegrees(degrees(acos(sin(radians(d1.degrees)) * sin(radians(d2.degrees))
                                + cos(radians(d1.degrees)) * cos(radians(d2.degrees))
                                * cos(radians(ra1.degrees) - radians(ra2.degrees)))))

class Cartesian():
    """
    A cartesian coordinate in 3D space.
    """
    def __init__(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z

    @classmethod
    def from_angular(cls, ra: DecimalDegrees, dec: DecimalDegrees) -> Cartesian:
        """
        Creates a 3D `Cartesian` coordinate on the surface of the unit sphere from
        angular coordinates.
        """
        a = radians(ra.degrees)
        b = radians(dec.degrees)
        save = cos(b)
        return Cartesian(save * cos(a), save * sin(a), sin(b))

def dist_sqr(p: Cartesian, q: Cartesian) -> float:
    """
    Returns the distance squared between two coordinates.
    """
    delta_x = (p.x - q.x)
    delta_y = (p.y - q.y)
    delta_z = (p.z - q.z)
    return delta_x * delta_x + delta_y * delta_y + delta_z * delta_z

def angle_between(p: Cartesian, q: Cartesian) -> DecimalDegrees:
    """
    Calculates the angle between the vectors (0, 0, 0) -> p and (0, 0, 0) -> q.
    """
    dot_product = p.x * q.x + p.y * q.y + p.z * q.z
    p_norm = (p.x * p.x + p.y * p.y + p.z * p.z) ** (0.5)
    q_norm = (q.x * q.x + q.y * q.y + q.z * q.z) ** (0.5)
    return DecimalDegrees(degrees(acos(dot_product / (p_norm * q_norm))))

def angular_separation_to_distance(angle: DecimalDegrees) -> float:
    """
    Converts an angular separation (in degrees) to a distance in 3D space.
    """
    p = Cartesian.from_angular(DecimalDegrees(0.0), DecimalDegrees(0.0))
    q = Cartesian.from_angular(angle, DecimalDegrees(0.0))
    if angle_between(p, q) != angle:
        raise Exception("WTF")

    return dist_sqr(p, q) ** 0.5
