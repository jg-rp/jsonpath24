"""JSON document nodes visited by a JSONPath query."""
from typing import List
from typing import Union


class JSONPathNode:
    """A JSON-like value and its location relative to the root of a JSON document.

    Attributes:
        value: The JSON-like value found at _location_.
        location: The parts of a normalized path to _value_.
        root: The target value at the top of the JSON node tree.
    """

    __slots__ = ("value", "location", "root")

    def __init__(
        self,
        value: object,
        location: List[Union[str, int]],
    ) -> None:
        self.value = value
        self.location = location

    def path(self) -> str:
        """The canonical string representation of the path to this node."""
        return "$" + "".join(f"[{repr(part)}]" for part in self.location)

    def __str__(self) -> str:
        return f"{self.value} at {self.path()}"


class JSONPathNodeList(List[JSONPathNode]):
    """A list of JSON documents nodes returned by JSONPath selectors."""

    def values(self) -> List[object]:
        """Return a list of values from each node in this list."""
        return [node.value for node in self]

    def values_or_singular(self) -> object:
        """Return a list of values or a single value if there's only one node."""
        if len(self) == 1:
            return self[0].value
        return self.values()
