"""Test Python JSONPath against the JSONPath Compliance Test Suite.

The CTS is a submodule located in /tests/cts. After a git clone, run
`git submodule update --init` from the root of the repository.
"""
import json
import operator
import unittest
from dataclasses import dataclass
from typing import Any
from typing import List
from typing import Mapping
from typing import Optional
from typing import Sequence
from typing import Union

import pytest

import jsonpath
from jsonpath.exceptions import JSONPathError


@dataclass
class Case:
    name: str
    selector: str
    document: Union[Mapping[str, Any], Sequence[Any], None] = None
    result: Any = None
    invalid_selector: Optional[bool] = None


SKIP = {
    "functions, match, filter, match function, unicode char class, uppercase": "\\p not supported",  # noqa: E501
    "functions, match, filter, match function, unicode char class negated, uppercase": "\\P not supported",  # noqa: E501
    "functions, search, filter, search function, unicode char class, uppercase": "\\p not supported",  # noqa: E501
    "functions, search, filter, search function, unicode char class negated, uppercase": "\\P not supported",  # noqa: E501
}


def cases() -> List[Case]:
    with open("tests/cts/cts.json", encoding="utf8") as fd:
        data = json.load(fd)
    return [Case(**case) for case in data["tests"]]


def valid_cases() -> List[Case]:
    return [case for case in cases() if not case.invalid_selector]


def invalid_cases() -> List[Case]:
    return [case for case in cases() if case.invalid_selector]


@pytest.mark.parametrize("case", valid_cases(), ids=operator.attrgetter("name"))
def test_compliance(case: Case) -> None:
    if case.name in SKIP:
        pytest.skip(reason=SKIP[case.name])

    assert case.document is not None

    test_case = unittest.TestCase()
    rv = jsonpath.query(case.selector, case.document).values()
    test_case.assertCountEqual(rv, case.result)  # noqa: PT009


# TODO: wrap libjsonpath exceptions
# @pytest.mark.parametrize("case", invalid_cases(), ids=operator.attrgetter("name"))
# def test_invalid_selectors(case: Case) -> None:
#     if case.name in SKIP:
#         pytest.skip(reason=SKIP[case.name])

#     with pytest.raises(JSONPathError):
#         jsonpath.compile(case.selector)
