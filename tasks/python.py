# type: ignore  # pylint: disable=unused-argument
from invoke import task


@task
def test(context):
    """
    Test with `pytest`
    """
    context.run("poetry run pytest")


@task(help={"source_dir": "Source files directory"})
def flake8(context, source_dir="src"):
    """
    Lint with `flake8`
    """
    context.run(f"poetry run flake8 {source_dir} tests")


@task(help={"source_dir": "Source files directory"})
def pylint(context, source_dir="src"):
    """
    Lint with `pylint`
    """
    context.run(f"poetry run pylint {source_dir} tests")


@task(flake8, pylint)
def lint(context):
    """
    Lint with all linting tools implemented
    """


@task(help={"source_dir": "Source files directory"})
def format_isort(context, source_dir="src"):
    """
    Sort imports with `isort`
    """
    context.run(f"poetry run isort {source_dir} tests")


@task(help={"source_dir": "Source files directory"})
def format_black(context, source_dir="src"):
    """
    Format files with `black`
    """
    context.run(f"poetry run black {source_dir} tests")


@task(pre=[format_isort, format_black], name="format")
def format_(context):
    """
    Format files and sort imports
    """


@task(help={"source_dir": "Source files directory"})
def format_check_isort(context, source_dir="src"):
    """
    Check whether imports are sorted correctly with `isort`
    """
    context.run(f"poetry run isort -context {source_dir} tests")


@task(help={"source_dir": "Source files directory"})
def format_check_black(context, source_dir="src"):
    """
    Check whether files are formatted correctly with `black`
    """
    context.run(f"poetry run black --check {source_dir} tests")


@task(format_check_isort, format_check_black)
def format_check(context):
    """
    Check whether files are formatted and imports are sorted as expected
    """


@task(name="type", help={"source_dir": "Source files directory"})
def type_(context, source_dir="src"):
    """
    Type check with `mypy`
    """
    context.run(f"poetry run mypy {source_dir}")


@task(format_check, lint, type_, test)
def test_all(context):
    """
    Run all code checks (formatting, linting, typing, testing)
    """


@task
def build(context):
    """
    Build Python packages
    """
    context.run("poetry build")


@task(build)
def publish(context):
    """
    Build and publish python packages to remote package registry
    """
    context.run(f"poetry publish")
