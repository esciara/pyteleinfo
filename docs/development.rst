Development environment
=======================

.. note::
    The choice of setup described in this page has been heavily influenced by the following references:

    * John Freeman's `project-template-python <https://github.com/thejohnfreeman/project-template-python>`_
    * Étienne Bersac's `Débuter avec Python en 2019 <https://bersace.cae.li/conseils-python-2019.html>`_
      (french), seen as a link from Sam (& Max)'s
      `Stack Python en 2019 <http://sametmax.com/stack-python-en-2019/>`_ (french)

    The two articles that definitely tipped the balance to go with ``poetry`` are:

    * `Poetically Packaging Your Python Project <https://hackersandslackers.com/poetic-python-project-packaging/>`_
    * `A deeper look into Pipenv and Poetry <https://frostming.com/2019/01-04/pipenv-poetry>`_

Tools used
----------

Main tools
~~~~~~~~~~

+------------------+--------------------------------------------------------------+-----------------+
| Tool             | Used features                                                | Unused features |
+==================+==============================================================+=================+
| ``pyenv``        | install the python environments on your host.                |                 |
+------------------+--------------------------------------------------------------+-----------------+
| ``poetry``       | package dependency                                           | versioning      |
|                  |                                                              |                 |
|                  | packaging                                                    |                 |
|                  |                                                              |                 |
|                  | package publishing                                           |                 |
+------------------+--------------------------------------------------------------+-----------------+
| ``invoke``       | running linting                                              |                 |
|                  |                                                              |                 |
|                  | running tests                                                |                 |
|                  |                                                              |                 |
|                  | generating the doc (sphinx)                                  |                 |
|                  |                                                              |                 |
|                  | serve generated doc                                          |                 |
+------------------+--------------------------------------------------------------+-----------------+
| ``tox``          | running code tests in multiple pythons environments          |                 |
+------------------+--------------------------------------------------------------+-----------------+
| ``bump2version`` | updating version (together with committing and tag creation) |                 |
+------------------+--------------------------------------------------------------+-----------------+
| ``black``        | linging: enforcing conformity to PEP8 (-ish)                 |                 |
+------------------+--------------------------------------------------------------+-----------------+
| ``isort``        | sorting python imports                                       |                 |
+------------------+--------------------------------------------------------------+-----------------+
| ``pylint``       | linting (*usage planned*)                                    |                 |
+------------------+--------------------------------------------------------------+-----------------+
| ``flake8``       | linting (*usage planned*)                                    |                 |
+------------------+--------------------------------------------------------------+-----------------+
| ``mypy``         | optional static typing (*usage planned*)                     |                 |
+------------------+--------------------------------------------------------------+-----------------+
| ``pytest``       | unit testing                                                 |                 |
+------------------+--------------------------------------------------------------+-----------------+
| ``coverage``     | coverage (*usage planned*)                                   |                 |
+------------------+--------------------------------------------------------------+-----------------+
| ``gitlab-ci``    | local CI pipeline and continuous delivery pipeline           |                 |
+------------------+--------------------------------------------------------------+-----------------+
| ``travis-ci``    | pull request CI pipeline on linux and mac                    |                 |
+------------------+--------------------------------------------------------------+-----------------+
| ``appveyor``     | pull request CI pipeline on windows                          |                 |
+------------------+--------------------------------------------------------------+-----------------+

Complementary tools
~~~~~~~~~~~~~~~~~~~

+--------------------------------+------------------------------------------------+-----------------+
| Tool                           | Used features                                  | Unused features |
+================================+================================================+=================+
| ``tox-virtualenv-no-download`` | disable virtualenv (>=14)'s downloading        |                 |
|                                | behaviour when running through tox.            |                 |
+--------------------------------+------------------------------------------------+-----------------+
| ``flake8-bugbear``             | B950 to follow `black's recommendations        |                 |
|                                | regarding line length handling by flake8`_     |                 |
+--------------------------------+------------------------------------------------+-----------------+
|                                |                                                |                 |
+--------------------------------+------------------------------------------------+-----------------+

.. _black's recommendations regarding line length handling by flake8: https://black.readthedocs.io/en/stable/the_black_code_style.html#line-length

Environment setup
-----------------

Prerequisites
~~~~~~~~~~~~~

`Install <https://github.com/pyenv/pyenv#installation>`_ ``pyenv``::

    # On Mac
    $ brew update
    $ brew install pyenv

Use ``pyenv global`` to `manage multiple versions at once <https://github.com/pyenv/pyenv/issues/92#issuecomment-31157539>`_.
Add first ``py36``, then others and others (at time of writing ``py37``, ``py38-dev``)::

    $ pyenv install 3.6.8
    $ pyenv install 3.7.3
    $ pyenv install 3.8-dev
    $ pyenv global 3.6.8 3.7.3 3.8-dev    # the first python version will be used as default version

`Install <https://poetry.eustace.io/docs/#installation>`_ ``poetry``::

    curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python

If you have publishing rights for the package, `setup repositories username and password <https://poetry.eustace.io/docs/repositories/#configuring-credentials>`_ for
``pypi``. Same for ``testpypi``, but after
`adding the url <https://poetry.eustace.io/docs/repositories/#adding-a-repository>`_::

    $ poetry config http-basic.pypi username password
    $ poetry config repositories.testpypi https://test.pypi.org/legacy/
    $ poetry config http-basic.testpypi username password

Actual setup
~~~~~~~~~~~~

Clone the project (or your fork of it) and move to the project directory::

    $ git clone https://github.com/esciara/pyteleinfo.git
    $ cd pyteleinfo

`Install the project's dependencies <https://poetry.eustace.io/docs/basic-usage/#installing-dependencies>`_::

    $ poetry install

Install ``black``'s `pre-commit hook <https://black.readthedocs.io/en/stable/version_control_integration.html>`_::

    $ pre-commit install

If you want to use your own local continuous integration server/continuous delivery pipeline,
install ``gitlab-ci`` using ``docker-compose`` (that you will have previously installed)
using code in `this repository <https://github.com/jeshan/gitlab-on-compose>`_::

    $ cd your/main/repositories/directory
    # Use gitlab_on_compose as a target cloning directory to avoid issues...
    $ git clone https://github.com/jeshan/gitlab-on-compose.git gitlab_on_compose
    $ docker-compose up

.. note:: You might want to reduce the number of gitlab-runners in you compose file to save resources.

Development tasks used/available
--------------------------------

Running tests::

    $ poetry run invoke test

Running black::

    $ poetry run black .

Running linting::

    $ poetry run invoke lint

Running generating the docs::

    $ poetry run invoke docs

Serving the generated docs to visually check them::

    $ poetry run invoke serve

Bumping version::

    $ poetry run bump2version patch    # used patch here, but use the argument your need

Building source and package distributions::

    $ poetry build

Publishing distributions to testpypi::

    $ poetry publish -r testpypi

    # If you want to build and publish in one go:
    $ poetry publish -r testpypi --build

Publishing distributions to pypi::

    $ poetry publish

.. note::

    Sphinx docs' publishing on http://readthedocs.org/ is done automatically through a ``github`` webhook setup
    from your account on the site.

Release workflow
--------------------

Reused with thanks from `Behave's repository <https://github.com/behave/behave/blob/master/tasks/release.py#L64>`_.

Pre-release checklist
~~~~~~~~~~~~~~~~~~~~~

* [ ] Everything is checked in
* [ ] All tests pass w/ tox

Release checklist
~~~~~~~~~~~~~~~~~

* [ ] Bump version to new-version and tag repository (via bump_version)
* [ ] Build packages (sdist, bdist_wheel via prepare)
* [ ] Register and upload packages to testpypi repository (first)
* [ ] Verify release is OK and packages from testpypi are usable
* [ ] Register and upload packages to pypi repository
* [ ] Push last changes to Github repository

Post-release checklist
~~~~~~~~~~~~~~~~~~~~~~

* [ ] Bump version to new-develop-version (via bump_version)
* [ ] Adapt CHANGES (if necessary)
* [ ] Commit latest changes to Github repository

IDE integration
---------------

* pylint integration (TODO: see
  https://medium.com/@wbrucek/how-i-integrated-pylint-into-my-pycharm-workflow-47047ce5e7fd ... plugin not working)
* black integration (TODO: see
  https://black.readthedocs.io/en/stable/editor_integration.html#pycharm-intellij-idea, or use plugin ?)

How to contribute
-----------------

TODO: Contribution file in repository.
