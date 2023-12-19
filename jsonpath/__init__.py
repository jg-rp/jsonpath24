from .env import JSONPathEnvironment
from .functions import FilterFunction
from .functions import FilterFunctionExpressionType
from .node import JSONPathNode
from .node import JSONPathNodeList

__all__ = (
    "FilterFunction",
    "FilterFunctionExpressionType",
    "JSONPathEnvironment",
    "JSONPathNode",
    "JSONPathNodeList",
)


# For convenience
DEFAULT_ENV = JSONPathEnvironment()
compile = DEFAULT_ENV.compile  # noqa: A001
query = DEFAULT_ENV.query
lazy_query = DEFAULT_ENV.lazy_query
# TODO: match
