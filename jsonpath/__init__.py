from libjsonpath import FilterFunction  # noqa: I001
from libjsonpath import ExpressionType
from libjsonpath import NOTHING
from .node import JSONPathNode
from .node import JSONPathNodeList
from .env import JSONPathEnvironment

__all__ = (
    "FilterFunction",
    "ExpressionType",
    "JSONPathEnvironment",
    "JSONPathNode",
    "JSONPathNodeList",
    "NOTHING",
)


# For convenience
DEFAULT_ENV = JSONPathEnvironment()
compile = DEFAULT_ENV.compile  # noqa: A001
query = DEFAULT_ENV.query
lazy_query = DEFAULT_ENV.lazy_query
# TODO: match
