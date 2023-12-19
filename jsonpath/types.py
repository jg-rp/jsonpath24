from typing import Sequence  # noqa: D100
from typing import Union

import libjsonpath

# TODO: is this necessary if we use from __future__ import annotations

Segments = Sequence[Union[libjsonpath.Segment, libjsonpath.RecursiveSegment]]

Selector = Union[
    libjsonpath.NameSelector,
    libjsonpath.IndexSelector,
    libjsonpath.WildSelector,
    libjsonpath.SliceSelector,
    libjsonpath.FilterSelector,
]

Expression = Union[
    libjsonpath.NullLiteral,
    libjsonpath.BooleanLiteral,
    libjsonpath.IntegerLiteral,
    libjsonpath.FloatLiteral,
    libjsonpath.StringLiteral,
    libjsonpath.LogicalNotExpression,
    libjsonpath.InfixExpression,
    libjsonpath.RelativeQuery,
    libjsonpath.RootQuery,
    libjsonpath.FunctionCall,
]
