import multiprocessing
import sys

import toml
from invoke import task

pty = sys.stdout.isatty()


def get_package_name() -> str:
    pyproject = toml.load(open("pyproject.toml", "r"))
    packages_list = [
        item["include"] for item in pyproject["tool"]["poetry"]["packages"]
    ]
    packages = " ".join(packages_list)
    return packages


@task
def lint(c):
    package_name = get_package_name()
    nproc = multiprocessing.cpu_count()

    someone_failed = False
    # skip mypy for the time being
    # c.run(f'mypy --config-file mypy.ini {package_name} tests', echo=True, pty=pty)
    if c.run(
        f"pylint --jobs {nproc} {package_name} tests", echo=True, pty=pty, warn=True
    ).failed:
        someone_failed = True
    if c.run(f"pydocstyle {package_name} tests", echo=True, pty=pty, warn=True).failed:
        someone_failed = True

    if someone_failed:
        sys.exit(1)


@task
def test(c):
    package_name = get_package_name()
    c.run(
        f"pytest --cov={package_name} --doctest-modules"
        f" --ignore=docs --ignore=tasks.py",
        echo=True,
        pty=pty,
    )


@task
def docs(c):
    c.run("make -C docs html", echo=True, pty=pty)


@task
def serve(c):
    c.run(
        "sphinx-autobuild docs docs/_build/html --host 0.0.0.0 --watch .",
        echo=True,
        pty=pty,
    )
