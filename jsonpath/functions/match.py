"""The standard `match` function extension."""

import re

from .filter_function import FilterFunction
from .filter_function import FilterFunctionExpressionType


class Match(FilterFunction):
    """A type-aware implementation of the standard `match` function."""

    arg_types = [FilterFunctionExpressionType.VALUE, FilterFunctionExpressionType.VALUE]
    return_type = FilterFunctionExpressionType.LOGICAL

    def __call__(self, string: str, pattern: str) -> bool:
        """Return `True` if _string_ matches _pattern_, or `False` otherwise."""
        try:
            # re.fullmatch caches compiled patterns internally
            return bool(re.fullmatch(pattern, string))
        except (TypeError, re.error):
            return False
