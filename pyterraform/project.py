"""A terraform project.
"""
from . import paths
from .config import Configuration, Data
from . import session
from .terraform import Command


class Project:  # pylint: disable=too-few-public-methods
    """A terraform project"""

    def __init__(self, cli_args: dict):
        self.path = paths.Paths(self)
        self.input = Data(self, cli_args)
        self.cfg = Configuration(self)
        self.tf = Command(self)  # pylint: disable=invalid-name
        self.session = session.Session(self)
