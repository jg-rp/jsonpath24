"""The standard `length` function extension."""
from collections.abc import Sized
from typing import Optional

from .filter_function import FilterFunction
from .filter_function import FilterFunctionExpressionType


class Length(FilterFunction):
    """A type-aware implementation of the standard `length` function."""

    arg_types = [FilterFunctionExpressionType.VALUE]
    return_type = FilterFunctionExpressionType.VALUE

    def __call__(self, obj: Sized) -> Optional[int]:
        """Return an object's length, or `None` if the object does not have a length."""
        try:
            return len(obj)
        except TypeError:
            return None
