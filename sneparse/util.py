from typing import TypeVar, Optional
import re
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm.session import Session

T = TypeVar("T")

def unwrap(x: Optional[T]) -> T:
    assert x is not None, "Attempt to unwrap None"
    return x

EPOCH_RE = re.compile(r"(?<=VLASS).+(?=\.ql)")
VERSION_RE = re.compile(r"(?<=\.v).+(?=\.I\.iter)")

def find_paths(session: Session, file_name: str, epoch: int) -> set[Path]:
    like = re.sub(VERSION_RE, "%", re.sub(EPOCH_RE, f"{epoch}.%", file_name))

    select_path_name = text(
        f"SELECT concat(path_to_file, file_name) FROM file_definition WHERE file_name LIKE '{like}';"
    )
    result = session.execute(select_path_name).all()

    return { Path("/projects/b1094/software/catalogs/").joinpath(row[0]) for row in result }

