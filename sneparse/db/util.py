from typing import Any

from sqlalchemy import text
from sqlalchemy.orm.session import Session

from sneparse.record import SneRecord
from sneparse.coordinates import DecimalDegrees

def paramterize(r: SneRecord) -> dict[str, Any]:
    """
    Construct the dictionary to be used as the parameters for the __init__ of
    an SQLAlchemy row class. Essentialy just `vars(r)` but converts the
    fields of type `DecimalDegrees` to `float`.
    """
    return {k: (v.degrees if isinstance(v, DecimalDegrees) else v) for k, v in vars(r).items()}

def prepare_q3c_index(table_name: str, session: Session) -> None:
    """
    Prepare `table_name` for fast cross matching
    """
    session.execute(text(
        f"""
        CREATE INDEX ON {table_name} (q3c_ang2ipix(right_ascension, declination));
        CLUSTER {table_name}_q3c_ang2ipix_idx ON {table_name};
        ANALYZE {table_name};
        """
    ))

