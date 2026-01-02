# pyteleinfo build automation with just
# Run `just` or `just --list` to see all available recipes

# Variables
package_dir := "teleinfo"

# Default recipe - show help
default:
    @just --list

# Setup targets
[group('setup')]
setup-dev-env-minimal: clean
    uv sync

[group('setup')]
setup-dev-env-full: clean
    uv sync --extra dev

[group('setup')]
setup-dev-host:
    ./scripts/install_pyenv.sh
    curl -LsSf https://astral.sh/uv/install.sh | sh
    @echo "Host setup correctly. Restart your shell or source your shell config file to be up and running :)"

[group('setup')]
setup-pre-commit-hooks:
    pre-commit install --hook-type pre-commit

[group('setup')]
setup-release-tools:
    npm install -g semantic-release@"^17.0.4"
    npm install -g @semantic-release/changelog@"^5.0.1"
    npm install -g @semantic-release/exec@"^5.0.0"
    npm install -g @semantic-release/git@"^9.0.0"
    npm install -g @semantic-release/github@"^7.0.5"

# CI/CD setup targets
[group('cicd-setup')]
setup-cicd-common:
    pip install --upgrade pip

[group('cicd-setup')]
setup-cicd-test-stage: setup-cicd-common
    git config --global user.name "Foo Bar"
    git config --global user.email "foo@bar.com"

[group('cicd-setup')]
setup-cicd-release-stage: setup-cicd-common

[group('cicd-setup')]
setup-cicd-publish-stage: setup-cicd-common

# Cleaning targets
[group('clean')]
clean: clean-build clean-pyc clean-test

[group('clean')]
clean-build:
    rm -fr build/
    rm -fr dist/
    rm -fr .eggs/
    find . -name '*.egg-info' -exec rm -fr {} +
    find . -name '*.egg' -exec rm -f {} +

[group('clean')]
clean-pyc:
    find . -name '*.pyc' -exec rm -f {} +
    find . -name '*.pyo' -exec rm -f {} +
    find . -name '*~' -exec rm -f {} +
    find . -name '__pycache__' -exec rm -fr {} +
    find . -name '.pytest_cache' -exec rm -fr {} +

[group('clean')]
clean-test:
    rm -fr .tox/
    rm -f .coverage
    rm -fr htmlcov/

[group('clean')]
clean-venv:
    rm -rf .venv

# Development REPL
[group('dev')]
repl:
    uv run bpython

# Linting targets
[group('quality')]
lint:
    uv run flake8 {{package_dir}} tests

[group('quality')]
pylint:
    uv run pylint {{package_dir}} tests

[group('quality')]
tox-lint:
    uv run tox -e lint

# Formatting targets
[group('quality')]
ruff-format:
    uv run ruff format src/{{package_dir}} tests

[group('quality')]
ruff-check:
    uv run ruff check --select I --fix src/{{package_dir}} tests

[group('quality')]
format: ruff-check ruff-format

[group('quality')]
format-check:
    uv run ruff check --select I src/{{package_dir}} tests
    uv run ruff format --check src/{{package_dir}} tests

[group('quality')]
tox-format:
    uv run tox -e format

# Type checking
[group('quality')]
type:
    uv run mypy -p {{package_dir}} -p tests

[group('quality')]
tox-type:
    uv run tox -e type

# Unit testing
[group('test')]
test:
    uv run pytest --cov={{package_dir}} --cov-report=html --cov-report=term tests

[group('test')]
tox-test-default-version: tox-py
alias tox-test := tox-test-default-version

[group('test')]
tox-py:
    uv run tox -e py

# BDD/Acceptance testing
[group('test')]
bdd:
    uv run behave features --format=pretty --tags=~wip --tags=~skip

[group('test')]
tox-bdd:
    uv run tox -e bdd
alias tox-bdd-default-version := tox-bdd

# All tests and checks
[group('test')]
tox:
    uv run tox

[group('test')]
tox-p:
    uv run tox -p auto

# Documentation
[group('docs')]
docs:
    uv run sphinx-apidoc -o docs/ {{package_dir}}
    $(MAKE) -C docs clean
    $(MAKE) -C docs html

[group('docs')]
docs-pdf:
    $(MAKE) -C docs latexpdf

[group('docs')]
tox-docs:
    uv run tox -e docs
    python -c "import os, webbrowser; webbrowser.open('file://' + os.path.abspath('docs/_build/html/index.html'))"

[group('docs')]
tox-docs-pdf:
    uv run tox -e docs-pdf

# Release targets
[group('release')]
cicd-release:
    npx semantic-release

[group('release')]
bump NEW_VERSION:
    uv run python -c "import tomli, tomli_w; f=open('pyproject.toml','rb'); d=tomli.load(f); f.close(); d['project']['version']='{{NEW_VERSION}}'; f=open('pyproject.toml','wb'); tomli_w.dump(d,f); f.close()"
    uv run python ./scripts/generate_version_file.py

[group('release')]
publish: clean
    uv run python scripts/verify_pypi_env_variables.py
    uv build
    #!/usr/bin/env bash
    repo_arg=""
    [ -n "$PYPI_REPOSITORY_NAME" ] && repo_arg="--publish-url $PYPI_REPOSITORY_NAME"
    uv publish $repo_arg

[group('release')]
install: clean
    uv sync --no-dev

# Install dependency groups (for automation)
[group('install-deps')]
install-test-dependencies:
    uv sync --no-dev

[group('install-deps')]
install-bdd-dependencies:
    uv sync --no-dev

[group('install-deps')]
install-format-dependencies:
    uv sync --no-dev

[group('install-deps')]
install-lint-dependencies:
    uv sync --no-dev

[group('install-deps')]
install-type-dependencies:
    uv sync --no-dev

[group('install-deps')]
install-docs-dependencies:
    uv sync --no-dev

# Git workflow helpers
[group('git')]
prune-branches:
    git remote prune origin
    git branch -vv | grep ': gone]' | grep -v "\\*" | awk '{ print $1; }' | xargs git branch -d

[group('git')]
prune-branches-force:
    git remote prune origin
    git branch -vv | grep ': gone]' | grep -v "\\*" | awk '{ print $1; }' | xargs git branch -D
alias pbf := prune-branches-force

[group('git')]
post-PR-merge-sync-step-1:
    git switch master
    git pull

[group('git')]
post-PR-merge-sync: post-PR-merge-sync-step-1 prune-branches-force
alias pms := post-PR-merge-sync
