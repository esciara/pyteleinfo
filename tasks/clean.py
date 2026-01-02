from invoke import task, Result


@task
def build(context):
    context.run("rm -fr build/")
    context.run("rm -fr dist/")
    context.run("rm -fr .eggs/")
    context.run("find . -name '*.egg-info' -exec rm -fr {} +")
    context.run("find . -name '*.egg' -exec rm -f {} +")


@task
def pyc(context):
    context.run("find . -name '*.pyc' -exec rm -f {} +")
    context.run("find . -name '*.pyo' -exec rm -f {} +")
    context.run("find . -name '*~' -exec rm -f {} +")
    context.run("find . -name '__pycache__' -exec rm -fr {} +")
    context.run("find . -name '.pytest_cache' -exec rm -fr {} +")


@task
def test(context):
    context.run("rm -fr .tox/")
    context.run("rm -f .coverage")
    context.run("rm -fr htmlcov/")


@task
def venv(context):
    result: Result = context.run("poetry env info -p")

    if result.failed:
        context.run("rm -fr .tox/")
    else:
        context.run("rm -rf $(poetry env info -p)")


@task(build, pyc, test, venv)
def all(context):
    pass
