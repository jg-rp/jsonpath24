"""The standard `value` function extension."""
from __future__ import annotations

from typing import TYPE_CHECKING

from .filter_function import FilterFunction
from .filter_function import FilterFunctionExpressionType
from .nothing import NOTHING

if TYPE_CHECKING:
    from jsonpath import JSONPathNodeList


class Value(FilterFunction):
    """A type-aware implementation of the standard `value` function."""

    arg_types = [FilterFunctionExpressionType.NODES]
    return_type = FilterFunctionExpressionType.VALUE

    def __call__(self, nodes: JSONPathNodeList) -> object:
        """Return the first node in a node list if it has only one item."""
        if len(nodes) == 1:
            return nodes[0].value
        return NOTHING
