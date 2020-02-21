"""Common path position.
"""
import sys
from pathlib import Path
import itertools

from .logs import logger
from .utils import error
from . import constants as const

class Paths:
    """Project relevant paths.
    The following structure is expected:
    /conf:           or what specified by configuration folders, for global options
    /<stack>/<env>/: proper TF stack
    /modules/:       shared modules
    /terraform:      binary of terraform
    /.run:           runtime files"""

    def __init__(self, project):
        self.project = project
        self._cache = dict()

    @property
    def root(self):
        """Terraform project root folder"""
        if not self._cache.get("root"):
            for i in range(0, 4):
                if (Path("../" * i) / self.conf_folder_name).is_dir():
                    self._cache["root"] = Path("../" * i).absolute().resolve()
                    logger.debug("Detected projct root at '%s'", self._cache["root"])
                    break
            else:
                error("Cannot locate project root folder, are you inside it?")
                sys.exit(const.RC_KO)
        return self._cache["root"]

    @property
    def conf_folder_name(self):
        """conf folder (into root)"""
        return self.project.cfg.tfw.confdir

    @property
    def terraform(self):
        """Terraform binary"""
        return self.root / "terraform"

    def get_stackinfo_from_cwd(self):
        """Find, if any, the stack name from the working directory"""
        try:
            children = Path.cwd().relative_to(self.root).parts
            meta = dict(itertools.zip_longest(const.STACK_FOLDER_STRUCTURE, children))
        except ValueError:
            logger.info("Terraform is not running from root project folder"
                        "Working dir is: %s - root dir is %s",
                        Path.cwd(), self.root)
        return meta

    @property
    def stack(self):
        """Stack path as, usually, <root>/<stack>/<env>.
        Such path could be defined from cli args or from cwd"""
        path = list()
        from_folder = self.get_stackinfo_from_cwd()
        for dir_ in const.STACK_FOLDER_STRUCTURE:
            if self.project.cfg.args.get(dir_):
                path.append(self.project.cfg.cli_argsi[dir_])
            elif from_folder.get(dir_):
                path.append(from_folder[dir_])
            else:
                raise ValueError("Not possible to identify stack path")
        return self.root.joinpath(*path)

    @property
    def modules(self):
        """Terraform modules folder"""
        return self.root / "modules"
    @property
    def conf(self):
        """Configuration folder for wrapper"""
        return self.root / self.conf_folder_name
    @property
    def conf_tfwrapper(self):
        """Configuration file for tfwrapper (YAML)"""
        return self.conf / 'config.yml'
    @property
    def conf_state(self):
        """Configuration file for state backends (YAML)"""
        return self.conf / 'state.yml'
    @property
    def stack_config(self):
        """Stack config file could be any of:
        - <root_dir>/conf/<stack>_<environment>_stack.yml
        - <root_dir>/<stack>/<environment>/stack.yml"""
        to_root = self.conf.joinpath(
            "_".join([self.project.cfg.stack_definition.stack,
                      self.project.cfg.stack_definition.environment,
                      "stack.yml"]))
        to_stack = self.stack.joinpath("stack.yml")
        if to_stack.is_file() and to_root.is_file():
            error("Not supported multiple configuration file."
                  f"Use one of '{to_stack}' or '{to_root}'")
            sys.exit(const.RC_KO)
        return to_stack or to_root
    @property
    def run(self):
        """Execution data"""
        return self.root / '.run'
