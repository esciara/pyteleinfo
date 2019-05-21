"""
Setup script for teleinfo.

USAGE:
    python setup.py install
    python setup.py nosetests

REQUIRES:
* setuptools >= 36.2.0

SEE ALSO:
* https://setuptools.readthedocs.io/en/latest/history.html
"""

import sys
import os.path

HERE0 = os.path.dirname(__file__) or os.curdir
os.chdir(HERE0)
HERE = os.curdir
sys.path.insert(0, HERE)

from setuptools import find_packages, setup

# -----------------------------------------------------------------------------
# CONFIGURATION:
# -----------------------------------------------------------------------------
python_version = float("%s.%s" % sys.version_info[:2])
TELEINFO = os.path.join(HERE, "teleinfo")
README = os.path.join(HERE, "README.md")
long_description = "".join(open(README).read())


# -----------------------------------------------------------------------------
# UTILITY:
# -----------------------------------------------------------------------------
def find_packages_by_root_package(where):
    """
    Better than excluding everything that is not needed,
    collect only what is needed.
    """
    root_package = os.path.basename(where)
    packages = ["%s.%s" % (root_package, sub_package)
                for sub_package in find_packages(where)]
    packages.insert(0, root_package)
    return packages


# -----------------------------------------------------------------------------
# SETUP:
# -----------------------------------------------------------------------------
setup(
    name='pyteleinfo',
    version='0.0.2',
    author='esciara',
    author_email='emmanuel.sciara@gmail.com',
    description='Serial access to ENEDIS teleinfo',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/esciara/pyteleinfo',
    # packages=[''],
    # package_dir={'': 'teleinfo'},
    packages=find_packages_by_root_package(TELEINFO),
    provides=["teleinfo"],
    entry_points={
        "console_scripts": [
            "teleinfo = teleinfo.__main__:main"
        ],
    },
    # -- REQUIREMENTS:
    # SUPPORT: python3.5 (or higher)
    python_requires=">=3.5",
    # TODO: ESC need to check what needs to be changed
    install_requires=[
        "pyserial",
        "pyserial-asyncio",
    ],
    test_suite="nose.collector",
    tests_require=[
        "pytest >= 3.0",
        "pytest-html >= 1.19.0",
        "nose >= 1.3",
        "mock >= 1.1",
        "PyHamcrest >= 1.8",
        "path.py >= 11.5.0"
    ],
    extras_require={
        "docs": [
            "sphinx >= 1.6",
            "sphinx_bootstrap_theme >= 0.6"
        ],
        "develop": [
            "coverage",
            "pytest >= 3.0",
            "pytest-html >= 1.19.0",
            "pytest.asyncio >= 0.10.0",
            "pytest-cov",
            "behave >= 1.2.6",
            "tox",
            "invoke >= 1.2.0",
            "path.py >= 11.5.0",
            "pycmd",
            "pylint",
        ],
    },
    # MAYBE-DISABLE: use_2to3
    use_2to3=bool(python_version >= 3.0),
    license="BSD",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: BSD License",
    ],
    zip_safe=True,
)
