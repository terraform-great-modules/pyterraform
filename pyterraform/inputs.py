"""Inputs placeholder."""
import os
import sys
import logging
from . import logger
from . import constants as const
from .cli_tools import parse_args

class Data:
    """Data configuration placeholder for:
    - cli arguments;
    - os environment
    - default paths
    """
    def __init__(self, project):
        self.project = project
        self._data = {'args': None,
                      'path': None,
                      'env': dict(os.environ)}

    @property
    def args(self):
        """Store cli arguments"""
        if self._data['args'] is None:
            args = sys.argv[1:]
            logger.debug("Command inputs: %r", args)
            self._data['args'] = vars(parse_args(self.project, args))
            if self._data['args'].get("debug"):
                logger.setLevel(logging.DEBUG)

        return self._data['args']
    @property
    def path(self):
        """Infos from cwd"""
        if self._data['path'] is None:
            self._data['path'] = self.project.path._get_stackinfo_from_cwd(const.CWD)  # pylint: disable=protected-access
        return self._data['path']
    @property
    def environment(self):
        """Environment configuration"""
        return self._data['env']
