"""A terraform project.
"""
import sys

from . import paths
from .config import Configuration
from . import inputs
from . import session
from . import constants as const
from .terraform import Command
from .logs import set_root_logger, get_logger, logger

log = get_logger(__name__, 'DEBUG')  # pylint: disable=invalid-name


class Project:  # pylint: disable=too-few-public-methods
    """A terraform project"""

    def __init__(self):
        self.path = paths.Paths(self)
        self.input = inputs.Data(self)
        self.cfg = Configuration(self)
        self.tf = Command(self)  # pylint: disable=invalid-name
        self.session = session.Session(self)
        self.enrich_logging()

    def enrich_logging(self):
        """Based on cli inputs, enrich logging"""
        if self.input.args.get('log_to_file') or self.input.environment.get('log_to_file') \
                or self.cfg.pyt.get('config.log_to_file'):
            set_root_logger(log_to_file=self.path.run() / "pyterraform.logs")
            logger.info("Enabled logging to file \"%s\"", self.path.run() / "pyterraform.logs")
            log.info("Enabled log to file for verbose analysis")

    def run(self):
        """Execute the command as request by cli input"""
        returncode = None
        # check terraform version
        #if args.subcommand not in ('foreach', 'providers', 'switchver', 'version'):
        #    self.tf.check_tf_version()
        #if args.subcommand in ["init", "bootstrap"]:
        #    self.tf.update_tf_providers()

        # run terraform finally!
        if self.cfg.pyt.get('config.tf_data_dir'):
            logger.info("Plan data will be cached on %s",
                        self.cfg.pyt.get('config.tf_data_dir').format(**self.cfg.stack.data))
        returncode = self.tf.run()
        log.info("The exit status is '%s'", returncode)
        if returncode is not None:
            sys.exit(returncode)
        else:
            sys.exit(const.RC_OK)
