from typing import Optional
from datetime import datetime
from dataclasses import dataclass
from sneparse.record import Source

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import DeclarativeBase

MASTER_TABLE_NAME  = "master"
CLEANED_TABLE_NAME = "cleaned"

class Base(DeclarativeBase):
    """
    Base class for declarative ORM.
    """
    pass

@dataclass
class SneRecordWrapper():
    """
    Wrapper around an `SneRecord` to be used with SQLAlchemy. To be inherited
    by other classes.
    """
    name           : Mapped[str]
    right_ascension: Mapped[Optional[float]]
    declination    : Mapped[Optional[float]]
    discover_date  : Mapped[Optional[datetime]]
    claimed_type   : Mapped[Optional[str]]
    source         : Mapped[Source]

@dataclass
class MasterRecord(Base, SneRecordWrapper):
    """
    A row in the table of all records.
    """
    __tablename__ = MASTER_TABLE_NAME
    
    id      : Mapped[int]           = mapped_column(primary_key=True)
    alias_of: Mapped[Optional[int]] = mapped_column(ForeignKey(f"{MASTER_TABLE_NAME}.id"), default=None)

    # Hash is necessary for when we construct a union-find of `MasterRecord`s
    def __hash__(self) -> int:
        return hash(repr(self))

@dataclass
class CleanedRecord(Base, SneRecordWrapper):
    """
    A row in the table of cleaned records (all sources are unique within
    the granularity of the cross matching).
    """
    __tablename__ =  CLEANED_TABLE_NAME

    cleaned_id: Mapped[int]           = mapped_column(primary_key=True)
    master_id : Mapped[Optional[int]] = mapped_column(ForeignKey(f"{MASTER_TABLE_NAME}.id"), default=None)

