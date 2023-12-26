"""A compiled JSONPath ready to be applied to a JSON-like object."""
from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING
from typing import Iterable
from typing import List
from typing import Mapping
from typing import NamedTuple
from typing import Sequence
from typing import Union

import libjsonpath

if TYPE_CHECKING:
    from .env import JSONPathEnvironment

from .functions import FilterFunction
from .functions import FilterFunctionExpressionType
from .functions.nothing import NOTHING  # XXX: move me
from .node import JSONPathNode
from .node import JSONPathNodeList

Segment = Union[
    "_Segment",
    "_RecursiveSegment",
]

Selector = Union[
    "_NameSelector",
    "_IndexSelector",
    "_WildSelector",
    "_SliceSelector",
    "_FilterSelector",
]

Expression = Union[
    "_NullLiteral",
    "_Literal",
    "_LogicalNotExpression",
    "_InfixExpression",
    "_RelativeQuery",
    "_RootQuery",
    "_FunctionCall",
]


class QueryContext(NamedTuple):
    """Per query contextual information."""

    env: JSONPathEnvironment
    root: object


class JSONPath:
    """A compiled JSONPath ready to be applied to a JSON-like object."""

    __slots__ = ("environment", "segments", "_segments")

    def __init__(
        self,
        *,
        environment: "JSONPathEnvironment",
        segments: Sequence[Union[libjsonpath.Segment, libjsonpath.RecursiveSegment]],
    ) -> None:
        self.environment = environment
        self.segments: List[Segment] = [
            _Segment(environment, s)
            if isinstance(s, libjsonpath.Segment)
            else _RecursiveSegment(environment, s)
            for s in segments
        ]

        self._segments = segments

    def __str__(self) -> str:
        return libjsonpath.to_string(self._segments)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, JSONPath) and self.segments == other.segments

    def query(self, obj: object) -> JSONPathNodeList:
        """Find all nodes in JSON-like value _obj_ matching this path."""
        return JSONPathNodeList(self.lazy_query(obj))

    def lazy_query(self, obj: object) -> Iterable[JSONPathNode]:
        """Generate nodes from _obj_ matching the this path."""
        context = QueryContext(root=obj, env=self.environment)
        nodes: Iterable[JSONPathNode] = [JSONPathNode(value=obj, location=[])]
        for segment in self.segments:
            nodes = segment.resolve(context, nodes)
        return nodes


class FilterContext(NamedTuple):
    """Info for evaluating filter expressions."""

    current: object
    query: QueryContext


def make_selector(
    environment: JSONPathEnvironment, selector: libjsonpath.Selector
) -> Selector:
    """Convert a libjsonpath selector to a Python selector."""
    if isinstance(selector, libjsonpath.NameSelector):
        return _NameSelector(selector)
    if isinstance(selector, libjsonpath.IndexSelector):
        return _IndexSelector(selector)
    if isinstance(selector, libjsonpath.WildSelector):
        return _WildSelector(selector)
    if isinstance(selector, libjsonpath.SliceSelector):
        return _SliceSelector(selector)
    assert isinstance(selector, libjsonpath.FilterSelector)
    return _FilterSelector(environment, selector)


def make_expression(  # noqa: PLR0911
    environment: JSONPathEnvironment, expr: libjsonpath.Expression
) -> Expression:
    """Convert a libjsonpath expression to a Python expression."""
    if isinstance(expr, libjsonpath.NullLiteral):
        return _NullLiteral(expr)
    if isinstance(
        expr,
        (
            libjsonpath.BooleanLiteral,
            libjsonpath.IntegerLiteral,
            libjsonpath.StringLiteral,
            libjsonpath.FloatLiteral,
        ),
    ):
        return _Literal(expr)
    if isinstance(expr, libjsonpath.LogicalNotExpression):
        return _LogicalNotExpression(environment, expr)
    if isinstance(expr, libjsonpath.InfixExpression):
        return _InfixExpression(environment, expr)
    if isinstance(expr, libjsonpath.RelativeQuery):
        return _RelativeQuery(environment, expr)
    if isinstance(expr, libjsonpath.RootQuery):
        return _RootQuery(environment, expr)
    assert isinstance(expr, libjsonpath.FunctionCall)
    return _FunctionCall(environment, expr)


class _Segment:
    __slots__ = ("token", "selectors")

    def __init__(
        self, environment: JSONPathEnvironment, segment: libjsonpath.Segment
    ) -> None:
        self.token = segment.token
        self.selectors = [
            make_selector(environment, selector) for selector in segment.selectors
        ]

    def resolve(
        self, context: QueryContext, nodes: Iterable[JSONPathNode]
    ) -> Iterable[JSONPathNode]:
        for node in nodes:
            for selector in self.selectors:
                yield from selector.resolve(context, node)


class _RecursiveSegment:
    __slots__ = ("token", "selectors")

    def __init__(
        self, environment: JSONPathEnvironment, segment: libjsonpath.RecursiveSegment
    ) -> None:
        self.token = segment.token
        self.selectors = [
            make_selector(environment, selector) for selector in segment.selectors
        ]

    def resolve(
        self, context: QueryContext, nodes: Iterable[JSONPathNode]
    ) -> Iterable[JSONPathNode]:
        for node in nodes:
            for descendant in self._visit(node):
                for selector in self.selectors:
                    yield from selector.resolve(context, descendant)

    def _visit(self, node: JSONPathNode) -> Iterable[JSONPathNode]:
        """Generate JSONPathNode instances recursively with _node_ at the root."""
        yield node
        if isinstance(node.value, Mapping):
            for key, val in node.value.items():
                if isinstance(val, str):
                    pass
                elif isinstance(val, (Mapping, Sequence)):
                    _node = JSONPathNode(
                        value=val,
                        location=node.location + [key],
                    )
                    yield from self._visit(_node)

        elif isinstance(node.value, Sequence) and not isinstance(node.value, str):
            for i, val in enumerate(node.value):
                if isinstance(val, str):
                    pass
                elif isinstance(val, (Mapping, Sequence)):
                    _node = JSONPathNode(
                        value=val,
                        location=node.location + [i],
                    )
                    yield from self._visit(_node)


class _NameSelector:
    __slots__ = ("token", "name")

    def __init__(self, selector: libjsonpath.NameSelector) -> None:
        self.token = selector.token
        self.name = selector.name

    def resolve(self, _: QueryContext, node: JSONPathNode) -> Iterable[JSONPathNode]:
        if isinstance(node.value, Mapping):
            with suppress(KeyError):
                yield JSONPathNode(
                    value=node.value[self.name],
                    location=node.location + [self.name],
                )


class _IndexSelector:
    __slots__ = ("token", "index")

    def __init__(self, selector: libjsonpath.IndexSelector) -> None:
        self.token = selector.token
        self.index = selector.index

    def resolve(self, _: QueryContext, node: JSONPathNode) -> Iterable[JSONPathNode]:
        if isinstance(node.value, Sequence) and not isinstance(node.value, str):
            norm_index = self._normalized_index(node.value, self.index)
            with suppress(IndexError):
                yield JSONPathNode(
                    value=node.value[self.index],
                    location=node.location + [norm_index],
                )

    def _normalized_index(self, obj: Sequence[object], index: int) -> int:
        if index < 0 and len(obj) >= abs(index):
            return len(obj) + index
        return index


class _WildSelector:
    __slots__ = ("token", "index")

    def __init__(self, selector: libjsonpath.WildSelector) -> None:
        self.token = selector.token

    def resolve(self, _: QueryContext, node: JSONPathNode) -> Iterable[JSONPathNode]:
        if isinstance(node.value, Mapping):
            for key, val in node.value.items():
                yield JSONPathNode(
                    value=val,
                    location=node.location + [key],
                )
        elif isinstance(node.value, Sequence) and not isinstance(node.value, str):
            for i, val in enumerate(node.value):
                yield JSONPathNode(
                    value=val,
                    location=node.location + [i],
                )


class _SliceSelector:
    __slots__ = ("token", "start", "stop", "step")

    def __init__(self, selector: libjsonpath.SliceSelector) -> None:
        self.token = selector.token
        self.start = selector.start
        self.stop = selector.stop
        self.step = selector.step

    def resolve(self, _: QueryContext, node: JSONPathNode) -> Iterable[JSONPathNode]:
        if (
            isinstance(node.value, Sequence)
            and not isinstance(node.value, str)
            and self.step != 0
        ):
            idx = self.start or 0
            step = self.step or 1
            for val in node.value[slice(self.start, self.stop, self.step)]:
                norm_index = self._normalized_index(node.value, idx)
                yield JSONPathNode(
                    value=val,
                    location=node.location + [norm_index],
                )
                idx += step

    def _normalized_index(self, obj: Sequence[object], index: int) -> int:
        if index < 0 and len(obj) >= abs(index):
            return len(obj) + index
        return index


class _FilterSelector:
    __slots__ = ("environment", "token", "expression")

    def __init__(
        self, environment: JSONPathEnvironment, selector: libjsonpath.FilterSelector
    ) -> None:
        self.token = selector.token
        self.expression = make_expression(environment, selector.expression)

    def resolve(
        self, context: QueryContext, node: JSONPathNode
    ) -> Iterable[JSONPathNode]:
        if isinstance(node.value, Sequence) and not isinstance(node.value, str):
            for i, val in enumerate(node.value):
                filter_context = FilterContext(
                    current=val,
                    query=context,
                )

                # Non empty node list or truthy
                rv = self.expression.resolve(filter_context)
                if (isinstance(rv, JSONPathNodeList) and len(rv) > 0) or _is_truthy(rv):
                    yield JSONPathNode(value=val, location=node.location + [i])

        elif isinstance(node.value, Mapping):
            for key, val in node.value.items():
                filter_context = FilterContext(
                    current=val,
                    query=context,
                )

                # Non empty node list or truthy
                rv = self.expression.resolve(filter_context)
                if (isinstance(rv, JSONPathNodeList) and len(rv) > 0) or _is_truthy(rv):
                    yield JSONPathNode(value=val, location=node.location + [key])


class _NullLiteral:
    __slots__ = ("token",)

    def __init__(self, expr: libjsonpath.NullLiteral) -> None:
        self.token = expr.token

    def resolve(self, _: FilterContext) -> object:
        return None


LiteralExpression = Union[
    libjsonpath.BooleanLiteral,
    libjsonpath.IntegerLiteral,
    libjsonpath.StringLiteral,
    libjsonpath.FloatLiteral,
]


class _Literal:
    __slots__ = ("token", "value")

    def __init__(self, expr: LiteralExpression) -> None:
        self.token = expr.token
        self.value = expr.value

    def resolve(self, _: FilterContext) -> object:
        return self.value


class _LogicalNotExpression:
    __slots__ = ("token", "expression")

    def __init__(
        self, environment: JSONPathEnvironment, expr: libjsonpath.LogicalNotExpression
    ) -> None:
        self.token = expr.token
        self.expression = make_expression(environment, expr.right)

    def resolve(self, context: FilterContext) -> object:
        return not _is_truthy(self.expression.resolve(context))


class _InfixExpression:
    __slots__ = ("token", "left", "op", "right")

    def __init__(
        self, environment: JSONPathEnvironment, expr: libjsonpath.InfixExpression
    ) -> None:
        self.token = expr.token
        self.left = make_expression(environment, expr.left)
        self.op = expr.op
        self.right = make_expression(environment, expr.right)

    def resolve(self, context: FilterContext) -> object:
        left = self.left.resolve(context)
        if isinstance(left, JSONPathNodeList) and len(left) == 1:
            left = left[0].value

        right = self.right.resolve(context)
        if isinstance(right, JSONPathNodeList) and len(right) == 1:
            right = right[0].value

        if self.op == libjsonpath.BinaryOperator.logical_and:
            return _is_truthy(left) and _is_truthy(right)

        if self.op == libjsonpath.BinaryOperator.logical_or:
            return _is_truthy(left) or _is_truthy(right)

        return _compare(left, self.op, right)


class _RelativeQuery:
    __slots__ = ("token", "path")

    def __init__(
        self, environment: JSONPathEnvironment, expr: libjsonpath.RelativeQuery
    ) -> None:
        self.token = expr.token
        self.path = JSONPath(environment=environment, segments=expr.query)

    def resolve(self, context: FilterContext) -> object:
        return self.path.query(context.current)


class _RootQuery:
    __slots__ = ("token", "path")

    def __init__(
        self, environment: JSONPathEnvironment, expr: libjsonpath.RootQuery
    ) -> None:
        self.token = expr.token
        self.path = JSONPath(environment=environment, segments=expr.query)

    def resolve(self, context: FilterContext) -> object:
        return self.path.query(context.query.root)


class _FunctionCall:
    __slots__ = ("token", "name", "args")

    def __init__(
        self, environment: JSONPathEnvironment, expr: libjsonpath.FunctionCall
    ) -> None:
        self.token = expr.token
        self.name = expr.name
        self.args = [make_expression(environment, arg) for arg in expr.args]

    def resolve(self, context: FilterContext) -> object:
        func = context.query.env.function_register.get(self.name)
        if not func:
            # TODO:
            raise Exception("undefined filter function " + self.name)

        args = [arg.resolve(context) for arg in self.args]
        return func(*_unpack_node_lists(func, args))


def _is_truthy(value: object) -> bool:
    if isinstance(value, JSONPathNodeList) and not value:
        # Empty node list.
        return False
    return not (isinstance(value, bool) and value is False)


def _compare(left: object, op: libjsonpath.BinaryOperator, right: object) -> bool:
    if op == libjsonpath.BinaryOperator.eq:
        return _eq(left, right)
    if op == libjsonpath.BinaryOperator.ne:
        return not _eq(left, right)
    if op == libjsonpath.BinaryOperator.lt:
        return _lt(left, right)
    if op == libjsonpath.BinaryOperator.gt:
        return _lt(right, left)
    if op == libjsonpath.BinaryOperator.ge:
        return _lt(right, left) or _eq(left, right)

    assert op == libjsonpath.BinaryOperator.le
    return _lt(left, right) or _eq(left, right)


def _eq(left: object, right: object) -> bool:  # noqa: PLR0911
    if isinstance(right, JSONPathNodeList):
        (left, right) = (right, left)

    if isinstance(left, JSONPathNodeList):
        if isinstance(right, JSONPathNodeList):
            if not left and not right:
                return True
            if len(left) == 1 and len(right) == 1:
                return left[0].value == right[0].value
        if not left:
            return right == NOTHING
        if len(left) == 1:
            return left[0].value == right
        return False

    if left == NOTHING and right == NOTHING:
        return True

    return left == right


def _lt(left: object, right: object) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return False

    if isinstance(left, str) and isinstance(right, str):
        return left < right

    # TODO: decimals?
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left < right

    return False


def _unpack_node_lists(func: FilterFunction, args: List[object]) -> List[object]:
    return [
        arg.values_or_singular()
        if isinstance(arg, JSONPathNodeList)
        and func.arg_types[i] != FilterFunctionExpressionType.NODES
        else arg
        for i, arg in enumerate(args)
    ]
