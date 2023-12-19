"""Classes modeling the JSONPath spec type system for function extensions."""
from abc import ABC
from abc import abstractmethod
from enum import Enum
from typing import TYPE_CHECKING
from typing import Any
from typing import List
from typing import Optional
from typing import Sequence

if TYPE_CHECKING:
    from jsonpath import JSONPathEnvironment

import libjsonpath

from jsonpath.exceptions import JSONPathTypeError
from jsonpath.types import Expression


class FilterFunctionExpressionType(Enum):
    """The type of a filter function argument or return value."""

    VALUE = 1
    LOGICAL = 2
    NODES = 3


class FilterFunction(ABC):
    """Base class for typed function extensions."""

    @property
    @abstractmethod
    def arg_types(self) -> List[FilterFunctionExpressionType]:
        """Argument types expected by the filter function."""

    @property
    @abstractmethod
    def return_type(self) -> FilterFunctionExpressionType:
        """The type of the value returned by the filter function."""

    @abstractmethod
    def __call__(self, *args: Any, **kwds: Any) -> Any:
        """Called the filter function."""

    def check_well_typedness(
        self,
        env: "JSONPathEnvironment",
        token: libjsonpath.Token,
        args: Sequence[Expression],
    ) -> None:
        """Raise a _JSONPathTypeError_ if _args_ are well-typed for this function."""
        # Correct number of arguments?
        if len(args) != len(self.arg_types):
            raise JSONPathTypeError(
                f"{token.value!r}() requires {len(self.arg_types)} arguments",
                token=token,
            )

        # Argument types
        for idx, typ in enumerate(self.arg_types):
            arg = args[idx]
            if typ == FilterFunctionExpressionType.VALUE:
                if not (
                    isinstance(
                        arg,
                        (
                            libjsonpath.NullLiteral,
                            libjsonpath.BooleanLiteral,
                            libjsonpath.IntegerLiteral,
                            libjsonpath.FloatLiteral,
                            libjsonpath.StringLiteral,
                        ),
                    )
                    or (
                        isinstance(
                            arg,
                            (
                                libjsonpath.RelativeQuery,
                                libjsonpath.RootQuery,
                            ),
                        )
                        and libjsonpath.singular_query(arg.query)
                    )
                    or (
                        self._function_return_type(env, arg)
                        == FilterFunctionExpressionType.VALUE
                    )
                ):
                    raise JSONPathTypeError(
                        f"{token.value}() argument {idx} must be of ValueType",
                        token=token,
                    )
            elif typ == FilterFunctionExpressionType.LOGICAL:
                if not isinstance(
                    arg,
                    (
                        libjsonpath.RelativeQuery,
                        libjsonpath.RootQuery,
                        libjsonpath.InfixExpression,
                    ),
                ):
                    raise JSONPathTypeError(
                        f"{token.value}() argument {idx} must be of LogicalType",
                        token=token,
                    )
            elif typ == FilterFunctionExpressionType.NODES and not (
                isinstance(arg, (libjsonpath.RelativeQuery, libjsonpath.RootQuery))
                or self._function_return_type(env, arg)
                == FilterFunctionExpressionType.NODES
            ):
                raise JSONPathTypeError(
                    f"{token.value}() argument {idx} must be of NodesType",
                    token=token,
                )

    def _function_return_type(
        self, env: "JSONPathEnvironment", expr: Expression
    ) -> Optional[FilterFunctionExpressionType]:
        """Return the type returned from a filter function.

        If _expr_ is not a `FunctionExtension` or the registered function definition is
        not type-aware, return `None`.
        """
        if not isinstance(expr, libjsonpath.FunctionCall):
            return None
        func = env.function_register.get(expr.name)
        if isinstance(func, FilterFunction):
            return func.return_type
        return None
