from pydantic_settings import BaseSettings, CliApp, CliSubCommand, SettingsConfigDict

from .commands import DiscoverCommand, PortCommand


class Application(BaseSettings):
    """pyteleinfo - ENEDIS teleinfo serial reader."""

    model_config = SettingsConfigDict(cli_prog_name="teleinfo")

    port: CliSubCommand[PortCommand]
    discover: CliSubCommand[DiscoverCommand]

    def cli_cmd(self) -> None:
        CliApp.run_subcommand(self)
