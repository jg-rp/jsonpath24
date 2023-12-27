"""A JSONPath configuration object including a filter function register."""
from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Dict
from typing import Iterable

from libjsonpath import FilterFunction
from libjsonpath import functions

from .path import JSONPath

if TYPE_CHECKING:
    from .node import JSONPathNode
    from .node import JSONPathNodeList

import libjsonpath


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
