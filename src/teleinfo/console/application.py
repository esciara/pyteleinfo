from cleo import Application as BaseApplication

from teleinfo import __version__

from .commands import DiscoveryCommand, PortCommand


class Application(BaseApplication):
    def __init__(self):
        super().__init__("PyTeleinfo", __version__)

        self.add(PortCommand())
        self.add(DiscoveryCommand())
