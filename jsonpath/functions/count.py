"""The standard `count` function extension."""
from __future__ import annotations

from typing import TYPE_CHECKING

from .filter_function import FilterFunction
from .filter_function import FilterFunctionExpressionType

if TYPE_CHECKING:
    from jsonpath import JSONPathNodeList


class Count(FilterFunction):
    """The built-in `count` function."""

    arg_types = [FilterFunctionExpressionType.NODES]
    return_type = FilterFunctionExpressionType.VALUE

    def __call__(self, node_list: JSONPathNodeList) -> int:
        """Return the number of nodes in the node list."""
        return len(node_list)
