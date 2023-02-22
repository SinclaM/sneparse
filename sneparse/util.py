from typing import TypeVar, Optional

T = TypeVar("T")

def unwrap(x: Optional[T]) -> T:
    assert x is not None, f"Attempt to unwrap None"
    return x
