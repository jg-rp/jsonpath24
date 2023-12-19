"""JSONPath exceptions."""
from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Optional

if TYPE_CHECKING:
    from libjsonpath import Token


class JSONPathError(Exception):
    """Base exception for all errors.

    Arguments:
        args: Arguments passed to `Exception`.
        token: The token that caused the error.
    """

    def __init__(self, *args: object, token: Optional[Token] = None) -> None:
        super().__init__(*args)
        self.token: Optional[Token] = token

    def __str__(self) -> str:
        msg = super().__str__()

        if not self.token:
            return msg

        return f"{msg}, ({self.token.query!r}:{self.token.index})"


class JSONPathSyntaxError(JSONPathError):
    """An exception raised when parsing a JSONPath string.

    Arguments:
        args: Arguments passed to `Exception`.
        token: The token that caused the error.
    """

    def __init__(self, *args: object, token: Token) -> None:
        super().__init__(*args)
        self.token = token


class JSONPathTypeError(JSONPathError):
    """An exception raised due to a type error.

    This should only occur at when evaluating filter expressions.
    """


class JSONPathIndexError(JSONPathError):
    """An exception raised when an array index is out of range.

    Arguments:
        args: Arguments passed to `Exception`.
        token: The token that caused the error.
    """

    def __init__(self, *args: object, token: Token) -> None:
        super().__init__(*args)
        self.token = token


class JSONPathNameError(JSONPathError):
    """An exception raised when an unknown function extension is called.

    Arguments:
        args: Arguments passed to `Exception`.
        token: The token that caused the error.
    """

    def __init__(self, *args: object, token: Token) -> None:
        super().__init__(*args)
        self.token = token
