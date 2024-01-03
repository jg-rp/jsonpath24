import re
from glob import glob

from pybind11.setup_helpers import Pybind11Extension
from pybind11.setup_helpers import build_ext
from setuptools import setup

with open("src/jsonpath24/__about__.py", encoding="utf-8") as fd:
    match = re.search(r'__version__ = "([0-9\.]+)"', fd.read())
    assert match
    __version__ = match.group(1)

with open("README.md", encoding="utf8") as fd:
    long_description = fd.read()

ext_modules = [
    Pybind11Extension(
        name="_jsonpath24",
        sources=[
            "src/jsonpath24/_jsonpath24.cpp",
            *sorted(glob("src/jsonpath24/_jsonpath24/*.cpp")),
        ],
        include_dirs=[
            "src/jsonpath24/_jsonpath24/",
        ],
        # XXX: Example: passing in the version to the compiled code
        define_macros=[("VERSION_INFO", __version__)],
    ),
]

setup(
    name="jsonpath24",
    package_dir={"", "src"},
    packages=["jsonpath24", "jsonpath24.functions"],
    version=__version__,
    url="https://github.com/jg-rp/jsonpath24",
    description="Fast JSONPath for Python.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    ext_modules=ext_modules,
    extras_require={"test": "pytest"},
    # Currently, build_ext only provides an optional "highest supported C++
    # level" feature, but in the future it may provide more features.
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
    python_requires=">=3.8",
    include_package_data=True,
    package_data={"": ["py.typed", "__init__.pyi"]},  # TODO:
)
