# type: ignore  # pylint: disable=unused-argument
from invoke import Collection

from . import clean, python

ns = Collection(
    python.build,
    python.flake8,
    python.format_,
    python.format_black,
    python.format_check,
    python.format_check_black,
    python.format_check_isort,
    python.format_isort,
    python.lint,
    python.publish,
    python.pylint,
    python.test,
    python.test_all,
    python.type_,
    clean,
)
