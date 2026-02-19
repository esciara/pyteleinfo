from pydantic_settings import CliApp

from .application import Application


def main():
    CliApp.run(Application)
