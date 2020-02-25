"""A terraform smart wrapper.

This script should let run terraform everywhere in a consistent way.
"""
import os
import sys
import logging
from copy import deepcopy

from . import constants as const
from .logs import logger
from . import config
from . import session
from . import project


def main():
    """Execute pyterraform wrapper."""
    stack = project.Project()
    return stack.run()


if __name__ == "__main__":
    main()
