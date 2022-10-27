from __future__ import annotations
from typing import Literal
from math import floor

HOURS_PER_DEGREE = 24.0 / 360.0
MINUTES_PER_HOUR = 60
SECONDS_PER_MINUTE = 60

class HoursMinutesSeconds():
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
        return self.sign == other.sign \
                and self.hours == other.hours \
                and self.minutes == other.minutes \
                and abs(self.seconds - other.seconds) < 1e-6

    @classmethod
    def fromDegrees(cls, d: Degrees) -> HoursMinutesSeconds:
        deg = d.degrees
        while deg > 360.0:
            deg -= 360.0

        hours   = floor(HOURS_PER_DEGREE * deg)
        deg -= hours / HOURS_PER_DEGREE
        minutes = floor(HOURS_PER_DEGREE * MINUTES_PER_HOUR * deg)
        deg -= minutes / (HOURS_PER_DEGREE * MINUTES_PER_HOUR)
        seconds = HOURS_PER_DEGREE * MINUTES_PER_HOUR * SECONDS_PER_MINUTE * deg

        return HoursMinutesSeconds(1, hours, minutes, seconds)

class Degrees():
    def __init__(self, degrees: float) -> None:
        self.degrees = degrees

    def __str__(self) -> str:
        return f"{self.degrees}°"

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other: Degrees) -> bool:
        return abs(self.degrees - other.degrees) < 1e-6

    @classmethod
    def fromHms(cls, hms: HoursMinutesSeconds) -> Degrees:
        return Degrees(hms.sign * (
            hms.hours / HOURS_PER_DEGREE
            + hms.minutes / (HOURS_PER_DEGREE * MINUTES_PER_HOUR)
            + hms.seconds / (HOURS_PER_DEGREE * MINUTES_PER_HOUR * SECONDS_PER_MINUTE)))
