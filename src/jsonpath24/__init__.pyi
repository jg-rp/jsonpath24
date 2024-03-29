from enum import Enum  # noqa: I001
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Union
from typing import overload

from ._env import JSONPathEnvironment
from ._path import JSONPath
from ._nothing import NOTHING
from ._nothing import Nothing
from .filter_function import FilterFunction

__all__ = (
    "BinaryOperator",
    "BooleanLiteral",
    "compile",
    "ExpressionType",
    "FilterFunction",
    "FilterSelector",
    "findall",
    "FloatLiteral",
    "FunctionCall",
    "FunctionExtensionMap",
    "FunctionExtensionTypes",
    "FunctionSignatureMap",
    "IndexSelector",
    "InfixExpression",
    "IntegerLiteral",
    "JSONPath",
    "JSONPathEnvironment",
    "JSONPathException",
    "JSONPathLexerError",
    "JSONPathNode",
    "JSONPathSyntaxError",
    "JSONPathTypeError",
    "Lexer",
    "LogicalNotExpression",
    "NameSelector",
    "NOTHING",
    "Nothing",
    "NullLiteral",
    "parse",
    "Parser",
    "query_",
    "RecursiveSegment",
    "RelativeQuery",
    "RootQuery",
    "Segment",
    "singular_query",
    "SliceSelector",
    "StringLiteral",
    "to_string",
    "Token",
    "TokenType",
    "WildSelector",
    "query",
    "compile",
    "findall",
)

class JSONPathException(Exception): ...  # noqa: N818
class JSONPathLexerError(JSONPathException): ...
class JSONPathSyntaxError(JSONPathException): ...
class JSONPathTypeError(JSONPathException): ...

class TokenType(Enum):
    eof_ = ...
    and_ = ...
    colon = ...
    comma = ...
    current = ...
    ddot = ...
    dq_string = ...
    eq = ...
    error = ...
    false_ = ...
    filter_ = ...
    float_ = ...
    func_ = ...
    ge = ...
    gt = ...
    index = ...
    int_ = ...
    lbracket = ...
    le = ...
    lparen = ...
    lt = ...
    name_ = ...
    ne = ...
    not_ = ...
    null_ = ...
    or_ = ...
    rbracket = ...
    root = ...
    rparen = ...
    sq_string = ...
    true_ = ...
    wild = ...

class Token:
    @property
    def type(self) -> TokenType: ...
    @property
    def value(self) -> str: ...
    @property
    def index(self) -> int: ...
    @property
    def query(self) -> str: ...

class Lexer:
    def __init__(self, query: str) -> None: ...
    def run(self) -> None: ...
    def tokens(self) -> Sequence[Token]: ...

class FunctionExtensionTypes:
    def __init__(self, args: List[ExpressionType], res: ExpressionType) -> None: ...
    @property
    def args(self) -> List[ExpressionType]: ...
    @property
    def res(self) -> ExpressionType: ...

class Parser:
    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(
        self, function_extensions: Dict[str, FunctionExtensionTypes]
    ) -> None: ...
    @overload
    def parse(self, tokens: List[Token]) -> Segments: ...
    @overload
    def parse(self, path: str) -> Segments: ...

class BinaryOperator(Enum):
    none = ...
    logical_and = ...
    logical_or = ...
    eq = ...
    ge = ...
    gt = ...
    le = ...
    lt = ...
    ne = ...

class ExpressionType(Enum):
    value = ...
    logical = ...
    nodes = ...

Segments = Sequence[Union["Segment", "RecursiveSegment"]]

Selector = Union[
    "NameSelector",
    "IndexSelector",
    "WildSelector",
    "SliceSelector",
    "FilterSelector",
]

Expression = Union[
    "NullLiteral",
    "BooleanLiteral",
    "IntegerLiteral",
    "FloatLiteral",
    "StringLiteral",
    "LogicalNotExpression",
    "InfixExpression",
    "RelativeQuery",
    "RootQuery",
    "FunctionCall",
]

class NullLiteral:
    @property
    def token(self) -> Token: ...

class BooleanLiteral:
    @property
    def token(self) -> Token: ...
    @property
    def value(self) -> bool: ...

class IntegerLiteral:
    @property
    def token(self) -> Token: ...
    @property
    def value(self) -> int: ...

class FloatLiteral:
    @property
    def token(self) -> Token: ...
    @property
    def value(self) -> float: ...

class StringLiteral:
    @property
    def token(self) -> Token: ...
    @property
    def value(self) -> str: ...

class LogicalNotExpression:
    @property
    def token(self) -> Token: ...
    @property
    def right(self) -> Expression: ...

class InfixExpression:
    @property
    def token(self) -> Token: ...
    @property
    def left(self) -> Expression: ...
    @property
    def op(self) -> BinaryOperator: ...
    @property
    def right(self) -> Expression: ...

class RelativeQuery:
    @property
    def token(self) -> Token: ...
    @property
    def query(self) -> Segments: ...

class RootQuery:
    @property
    def token(self) -> Token: ...
    @property
    def query(self) -> Segments: ...

class FunctionCall:
    @property
    def token(self) -> Token: ...
    @property
    def name(self) -> str: ...
    @property
    def args(self) -> Sequence[Expression]: ...

class NameSelector:
    @property
    def token(self) -> Token: ...
    @property
    def name(self) -> str: ...
    @property
    def shorthand(self) -> bool: ...

class IndexSelector:
    @property
    def token(self) -> Token: ...
    @property
    def index(self) -> int: ...

class WildSelector:
    @property
    def token(self) -> Token: ...
    @property
    def shorthand(self) -> bool: ...

class SliceSelector:
    @property
    def token(self) -> Token: ...
    @property
    def start(self) -> Optional[int]: ...
    @property
    def stop(self) -> Optional[int]: ...
    @property
    def step(self) -> Optional[int]: ...

class FilterSelector:
    @property
    def token(self) -> Token: ...
    @property
    def expression(self) -> Expression: ...

class Segment:
    @property
    def token(self) -> Token: ...
    @property
    def selectors(self) -> Sequence[Selector]: ...

class RecursiveSegment:
    @property
    def token(self) -> Token: ...
    @property
    def selectors(self) -> Sequence[Selector]: ...

def parse(query: str) -> Segments: ...
def to_string(segments: Segments) -> str: ...
def singular_query(segments: Segments) -> bool: ...

class JSONPathNode:
    @property
    def value(self) -> object: ...
    @property
    def location(self) -> List[Union[int, str]]: ...
    def path(self) -> str: ...

JSONPathNodeList = Sequence[JSONPathNode]

class FunctionExtensionMap(Dict[str, FilterFunction]): ...
class FunctionSignatureMap(Dict[str, FunctionExtensionTypes]): ...

@overload
def query_(
    segments: Segments,
    data: object,
    functions: FunctionExtensionMap,
    signatures: FunctionSignatureMap,
    nothing: object,
) -> List[JSONPathNode]: ...
@overload
def query_(
    path: str,
    data: object,
    functions: FunctionExtensionMap,
    signatures: FunctionSignatureMap,
    nothing: object,
) -> List[JSONPathNode]: ...

class Env_:  # noqa: N801
    def __init__(
        self,
        functions: FunctionExtensionMap,
        signatures: FunctionSignatureMap,
        nothing: object,
    ) -> None: ...
    def query(self, path: str, data: object) -> List[JSONPathNode]: ...
    def from_segments(self, segments: Segments, data: object) -> List[JSONPathNode]: ...
    def parse(self, path: str) -> Segments: ...

def compile(path: str) -> JSONPath: ...  # noqa: A001
def findall(path: str, data: object) -> List[object]: ...
def query(path: str, data: object) -> List[JSONPathNode]: ...
