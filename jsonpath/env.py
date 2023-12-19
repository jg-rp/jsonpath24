"""A JSONPath configuration object including a filter function register."""
from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Dict
from typing import Iterable

from . import functions
from .path import JSONPath

if TYPE_CHECKING:
    from .functions import FilterFunction
    from .node import JSONPathNode
    from .node import JSONPathNodeList

import libjsonpath

from .exceptions import JSONPathNameError

if TYPE_CHECKING:
    from .types import Expression
    from .types import Segments


class JSONPathEnvironment:
    """JSONPath configuration."""

    def __init__(self) -> None:
        self.function_register: Dict[str, FilterFunction] = {}
        self.setup_function_register()

    def setup_function_register(self) -> None:
        """Initialize function extensions."""
        self.function_register["length"] = functions.Length()
        self.function_register["count"] = functions.Count()
        self.function_register["match"] = functions.Match()
        self.function_register["search"] = functions.Search()
        self.function_register["value"] = functions.Value()

    def compile(self, query: str) -> JSONPath:  # noqa: A003
        """Prepare a JSONPath query string for matching against JSON-like data."""
        segments = libjsonpath.parse(query)
        # XXX: self._check_filter_function_well_typedness(segments)
        return JSONPath(environment=self, segments=segments)

    def query(self, path: str, obj: object) -> JSONPathNodeList:
        """Match JSONPath _path_ against JSON-like data _obj_."""
        return self.compile(path).query(obj)

    def lazy_query(self, path: str, obj: object) -> Iterable[JSONPathNode]:
        """Match JSONPath _path_ against JSON-like data _obj_."""
        return self.compile(path).lazy_query(obj)

    def _check_filter_function_well_typedness(self, segments: Segments) -> None:
        for segment in segments:
            for selector in segment.selectors:
                if isinstance(selector, libjsonpath.FilterSelector):
                    for func_call in self._function_calls(selector.expression):
                        try:
                            func = self.function_register[func_call.name]
                        except KeyError as err:
                            raise JSONPathNameError(
                                f"function {func_call.token.value!r} is not defined",
                                token=func_call.token,
                            ) from err
                        func.check_well_typedness(self, func_call.token, func_call.args)

    def _function_calls(
        self, expression: Expression
    ) -> Iterable[libjsonpath.FunctionCall]:
        if isinstance(expression, libjsonpath.FunctionCall):
            yield expression
        elif isinstance(expression, libjsonpath.LogicalNotExpression):
            yield from self._function_calls(expression.right)
        elif isinstance(expression, libjsonpath.InfixExpression):
            yield from self._function_calls(expression.left)
            yield from self._function_calls(expression.right)
        elif isinstance(expression, (libjsonpath.RootQuery, libjsonpath.RelativeQuery)):
            for segment in expression.query:
                for selector in segment.selectors:
                    if isinstance(selector, libjsonpath.FilterSelector):
                        yield from self._function_calls(selector.expression)
