"""Common path position.
"""
import sys
from pathlib import Path
import itertools

from .logs import logger
from .utils import error
from . import constants as const


class Conf:
    """Pyterraform configuration directory"""
    def __init__(self, paths):
        self.paths = paths

    def __call__(self):
        return self.paths.root() / const.CONF_DIR

    def pyterraform(self):
        """Configuration file for tfwrapper (YAML)"""
        return self() / 'pyterraform.yml'

    def state(self):
        """Configuration file for state backends (YAML)"""
        return self() / 'state.yml'

class Stack:
    """Stack directory"""
    def __init__(self, paths):
        self.paths = paths

    def __call__(self):
        if not self.paths._cache.get('stack'):
            self.paths._cache['stack'] = self.paths.get_stack_path(const.CWD)
        return self.paths._cache['stack']

    def config(self):
        """Stack config file as:
        - <root_dir>/<stack/path/definition>/stack.yml"""
        return self() / 'stack.yml'


class Paths:
    """Project relevant paths.
    The following structure is expected:
    /pyterraform:    global options of the project and the wrapper
    /<stack>/<env>/: proper TF stack (or what specified into pyterraform conf)
    /modules/:       shared modules cacheing
    /terraform:      binary of terraform
    /.run:           runtime files"""

    def __init__(self, project):
        self.project = project
        self._cache = dict()

    def root(self):
        """Wrapper root folder"""
        if not self._cache.get("root"):
            for i in range(0, 5):
                if (Path("../" * i) / const.CONF_DIR).is_dir():
                    self._cache["root"] = Path("../" * i).absolute().resolve()
                    logger.debug("Detected root folder at '%s'",
                                 self._cache["root"])
                    break
            else:
                error("Cannot locate project root folder, are you inside it?")
                sys.exit(const.RC_KO)
        return self._cache["root"]

    @property
    def conf(self):
        """Pyterraform configuration directory (under root path)"""
        return Conf(self)

    def terraform(self):
        """Terraform binary"""
        return self.root() / "terraform"

    def _get_stackinfo_from_cwd(self, path=None):
        """Find, if any, the stack name from the working directory"""
        path = Path(path) if path else Path.cwd()
        try:
            children = path.relative_to(self.root()).parts
            meta = dict(itertools.zip_longest(self.project.cfg.pyt.stack_folder_structure,
                                              children))
        except ValueError:
            logger.info("Terraform is not running from root project folder"
                        "Working dir is: %s - root dir is %s",
                        path, self.root())
        return meta

    def get_stack_path(self, path=None):
        """Compute from cwd the stack path"""
        meta = self._get_stackinfo_from_cwd(path)
        path = Path()
        for dir_ in self.project.cfg.pyt.stack_folder_structure:
            path = path / meta[dir_]
        return self.root() / path

    @property
    def stack(self):
        """Stack path as, usually, <root>/<stack>/<env>.
        Such path could be defined from cli args or from cwd"""
        return Stack(self)

    def modules(self):
        """Terraform modules folder"""
        return self.root() / "modules"

    def run(self):
        """Execution data"""
        dir_ = self.root() / '.run'
        if not dir_.is_dir():
            dir_.mkdir(exist_ok=True)
        return self.root() / '.run'
