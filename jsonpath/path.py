"""A compiled JSONPath ready to be applied to a JSON-like object."""
from __future__ import annotations

from contextlib import suppress
from operator import getitem
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
    from .types import Expression
    from .types import Segments
    from .types import Selector

from .functions import FilterFunction
from .functions import FilterFunctionExpressionType
from .functions.nothing import NOTHING
from .node import JSONPathNode
from .node import JSONPathNodeList


class FilterContext(NamedTuple):
    """Info for evaluating filter expressions."""

    current: object
    root: object


class JSONPath:
    """A compiled JSONPath ready to be applied to a JSON-like object."""

    __slots__ = ("environment", "segments")

    def __init__(
        self,
        *,
        environment: "JSONPathEnvironment",
        segments: Segments,
    ) -> None:
        self.environment = environment
        self.segments = segments

    def __str__(self) -> str:
        return libjsonpath.to_string(self.segments)

    # TODO: __eq__ on segments?

    def query(self, obj: object) -> JSONPathNodeList:
        """Find all nodes in JSON-like value _obj_ matching this path."""
        return JSONPathNodeList(self.lazy_query(obj))

    def lazy_query(self, obj: object) -> Iterable[JSONPathNode]:
        """Generate nodes from _obj_ matching the this path."""
        nodes: Iterable[JSONPathNode] = [JSONPathNode(value=obj, location=[], root=obj)]
        for segment in self.segments:
            nodes = self._resolve_segment(nodes, segment)
        return nodes

    def _resolve_segment(
        self,
        nodes: Iterable[JSONPathNode],
        segment: Union[libjsonpath.Segment, libjsonpath.RecursiveSegment],
    ) -> Iterable[JSONPathNode]:
        if isinstance(segment, libjsonpath.Segment):
            for node in nodes:
                for selector in segment.selectors:
                    yield from self._resolve_selector(node, selector)

        elif isinstance(segment, libjsonpath.RecursiveSegment):
            for node in nodes:
                for descendant in self._visit(node):
                    for selector in segment.selectors:
                        yield from self._resolve_selector(descendant, selector)

    def _resolve_selector(  # noqa: PLR0912
        self, node: JSONPathNode, selector: Selector
    ) -> Iterable[JSONPathNode]:
        if isinstance(selector, libjsonpath.NameSelector):
            if isinstance(node.value, Mapping):
                with suppress(KeyError):
                    yield JSONPathNode(
                        value=getitem(node.value, selector.name),
                        location=node.location + [selector.name],
                        root=node.root,
                    )

        elif isinstance(selector, libjsonpath.IndexSelector):
            if isinstance(node.value, Mapping):
                # XXX: Try the string representation of the index as a key.
                with suppress(KeyError):
                    yield JSONPathNode(
                        value=getitem(node.value, str(selector.index)),
                        location=node.location + [str(selector.index)],
                        root=node.root,
                    )
            elif isinstance(node.value, Sequence) and not isinstance(node.value, str):
                norm_index = self._normalized_index(node.value, selector.index)
                with suppress(IndexError):
                    yield JSONPathNode(
                        value=getitem(node.value, selector.index),
                        location=node.location + [norm_index],
                        root=node.root,
                    )

        elif isinstance(selector, libjsonpath.WildSelector):
            if isinstance(node.value, Mapping):
                for key, val in node.value.items():
                    yield JSONPathNode(
                        value=val,
                        location=node.location + [key],
                        root=node.root,
                    )
            elif isinstance(node.value, Sequence) and not isinstance(node.value, str):
                for i, val in enumerate(node.value):
                    yield JSONPathNode(
                        value=val,
                        location=node.location + [i],
                        root=node.root,
                    )

        elif isinstance(selector, libjsonpath.SliceSelector):
            if (
                isinstance(node.value, Sequence)
                and not isinstance(node.value, str)
                and selector.step != 0
            ):
                idx = selector.start or 0
                step = selector.step or 1
                for val in getitem(
                    node.value, slice(selector.start, selector.stop, selector.step)
                ):
                    norm_index = self._normalized_index(node.value, idx)
                    yield JSONPathNode(
                        value=val,
                        location=node.location + [norm_index],
                        root=node.root,
                    )
                    idx += step

        elif isinstance(selector, libjsonpath.FilterSelector):
            if isinstance(node.value, Sequence) and not isinstance(node.value, str):
                for i, val in enumerate(node.value):
                    filter_context = FilterContext(
                        current=val,
                        root=node.root,
                    )

                    # Non empty node list or truthy
                    rv = self._resolve_expression(selector.expression, filter_context)
                    if (
                        isinstance(rv, JSONPathNodeList) and len(rv) > 0
                    ) or self._is_truthy(rv):
                        yield JSONPathNode(
                            value=val, location=node.location + [i], root=node.root
                        )

            elif isinstance(node.value, Mapping):
                for key, val in node.value.items():
                    filter_context = FilterContext(
                        current=val,
                        root=node.root,
                    )

                    # Non empty node list or truthy
                    rv = self._resolve_expression(selector.expression, filter_context)
                    if (
                        isinstance(rv, JSONPathNodeList) and len(rv) > 0
                    ) or self._is_truthy(rv):
                        yield JSONPathNode(
                            value=val, location=node.location + [key], root=node.root
                        )

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
                        root=node.root,
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
                        root=node.root,
                    )
                    yield from self._visit(_node)

    def _normalized_index(self, obj: Sequence[object], index: int) -> int:
        if index < 0 and len(obj) >= abs(index):
            return len(obj) + index
        return index

    def _resolve_expression(  # noqa: PLR0911
        self,
        expression: Expression,
        context: FilterContext,
    ) -> object:
        if isinstance(expression, libjsonpath.NullLiteral):
            return None

        if isinstance(
            expression,
            (
                libjsonpath.BooleanLiteral,
                libjsonpath.IntegerLiteral,
                libjsonpath.StringLiteral,
                libjsonpath.FloatLiteral,
            ),
        ):
            return expression.value

        if isinstance(expression, libjsonpath.LogicalNotExpression):
            return not self._is_truthy(
                self._resolve_expression(expression.right, context)
            )

        if isinstance(expression, libjsonpath.InfixExpression):
            left = self._resolve_expression(expression.left, context)
            if isinstance(left, JSONPathNodeList) and len(left) == 1:
                left = left[0].value

            right = self._resolve_expression(expression.right, context)
            if isinstance(right, JSONPathNodeList) and len(right) == 1:
                right = right[0].value

            if expression.op == libjsonpath.BinaryOperator.logical_and:
                return self._is_truthy(left) and self._is_truthy(right)

            if expression.op == libjsonpath.BinaryOperator.logical_or:
                return self._is_truthy(left) or self._is_truthy(right)

            return self._compare(left, expression.op, right)

        if isinstance(expression, libjsonpath.RelativeQuery):
            path = JSONPath(
                environment=self.environment,
                segments=expression.query,
            )

            return path.query(context.current)

        if isinstance(expression, libjsonpath.RootQuery):
            return JSONPath(
                environment=self.environment,
                segments=expression.query,
            ).query(context.root)

        if isinstance(expression, libjsonpath.FunctionCall):
            func = self.environment.function_register.get(expression.name)
            if not func:
                # TODO:
                raise Exception("undefined filter function " + expression.name)

            args = [self._resolve_expression(arg, context) for arg in expression.args]
            return func(*self._unpack_node_lists(func, args))

        # XXX:
        raise Exception(f"unknown expression {expression!r}")

    def _is_truthy(self, value: object) -> bool:
        if isinstance(value, JSONPathNodeList) and not value:
            # Empty node list.
            return False
        return not (isinstance(value, bool) and value is False)

    def _compare(
        self, left: object, op: libjsonpath.BinaryOperator, right: object
    ) -> bool:
        if op == libjsonpath.BinaryOperator.eq:
            return self._eq(left, right)
        if op == libjsonpath.BinaryOperator.ne:
            return not self._eq(left, right)
        if op == libjsonpath.BinaryOperator.lt:
            return self._lt(left, right)
        if op == libjsonpath.BinaryOperator.gt:
            return self._lt(right, left)
        if op == libjsonpath.BinaryOperator.ge:
            return self._lt(right, left) or self._eq(left, right)

        assert op == libjsonpath.BinaryOperator.le
        return self._lt(left, right) or self._eq(left, right)

    def _eq(self, left: object, right: object) -> bool:  # noqa: PLR0911
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

    def _lt(self, left: object, right: object) -> bool:
        if isinstance(left, bool) or isinstance(right, bool):
            return False

        if isinstance(left, str) and isinstance(right, str):
            return left < right

        # TODO: decimals?
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return left < right

        return False

    def _unpack_node_lists(
        self, func: FilterFunction, args: List[object]
    ) -> List[object]:
        return [
            arg.values_or_singular()
            if isinstance(arg, JSONPathNodeList)
            and func.arg_types[i] != FilterFunctionExpressionType.NODES
            else arg
            for i, arg in enumerate(args)
        ]
