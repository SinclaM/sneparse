from typing import Optional, Literal, Tuple

class HoursMinutesSeconds():
    def __init__(self, sign: Literal[-1, 1], hours: int, minutes: int, seconds: float) -> None:
        self.sign    = sign
        self.hours   = hours
        self.minutes = minutes
        self.seconds = seconds

    def __str__(self) -> str:
        return f"{'+' if self.sign == 1 else '-'}{self.hours:02}:{self.minutes:02}:{self.seconds}"

class Degrees():
    def __init__(self, degrees: float) -> None:
        self.degrees = degrees

    def __str__(self) -> str:
        return f"{self.degrees}°"

