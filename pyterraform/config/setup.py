"""Configuration object storage for pyterraform and stacks"""
from abc import ABC, abstractmethod
import sys
from pathlib import Path
import yaml
from schema import Schema, Optional, Or, SchemaError
from .. import constants as const
from ..logs import logger


# pylint: disable=too-few-public-methods,missing-function-docstring
class Setups(ABC):
    """Generic setup placeholder"""

    def __init__(self, project):
        self._data = None
        self.project = project

    @property
    def data(self):
        """Raw data (please don't change)"""
        if self._data is None:
            self.load_data()
        return self._data
    def _get(self, path, default=None):
        data = self.data
        try:
            for item in path.split('.'):
                data = data[item]
            return data
        except KeyError:
            return default
    def _set(self, path, value):
        data = self.data
        for key in path.split('.')[:-1]:
            data = data.setdefault(key, dict())
        data[path.split('.')[-1]] = value
    def get(self, path, default=None):
        """Extract wanted value"""
        return self._get(path, default)
    @abstractmethod
    def load_data(self):
        """Load data from proper sources"""
        return


class Pyterraform(Setups):
    """Set up of pyterraform wrapper"""
    def load_data(self):
        """Load data from state and conf, interpolate with args"""
        state = self._load_state()
        config = self._load_config()
        self._data = {'state': state,
                      'config': config}

    @property
    def stack_folder_structure(self):
        """Structure of folder"""
        return self._get('config.folder_structure').split('.')
    @property
    def _state_schema(self):
        """Schema validation and defaults"""
        return Schema( \
    {Optional('profile'): str,
     Optional('region'): str,
     Optional('assume_role'): str,
     Optional('backend'): {Optional('s3'): {
         'bucket': str,
         'key': str,
         'dynamodb_table': str,
         Optional('acl', default='private'): str}}})

    def _load_state(self):
        """Load state example"""
        if not self.project.path.conf.state().is_file():
            logger.warning("No state configuration file found!")
            return dict()
        with self.project.path.conf.state().open() as _f:
            logger.debug("Loading state config from '%s'", self.project.path.conf.state())
            config = yaml.safe_load(_f)
        try:
            state = self._state_schema.validate(config)
            return state
        except SchemaError as ex:
            logger.error('Configuration error in %s : %s',
                         self.project.path.conf.state(), ex)
            sys.exit(const.RC_KO)

    @property
    def _config_schema(self):
        """Schema validation and defaults"""
        return Schema({ \
    Optional('always_trigger_init', default=False): bool,
    Optional('pipe_plan_command', default='cat'): str,
    Optional('folder_structure', default='stack.environment'): str,
    Optional('tf_version', default='0.12.21'): str,
    Optional('tf_binary_cache', default=Path.home() / '.terraform' / 'binaries'): str,})
#    Optional('tf_plugin_dir', default='/tmp/terraform.d/plugin'): str,
#    Optional('tf_data_dir', default='/tmp/terraform.d/data/{stack}/{environment}'): str})

    def _load_config(self):
        """Load config example"""
        try:
            with self.project.path.conf.pyterraform().open() as _f:
                logger.debug("Loading pyterraform wrapper config from '%s'",
                             self.project.path.conf.pyterraform())
                config = yaml.safe_load(_f)
        except FileNotFoundError:
            logger.warning("No pyterraform configuration file found!")
            config = dict()
        try:
            config = self._config_schema.validate(config)
            return config
        except SchemaError as ex:
            logger.error('Configuration error in %s : %s',
                         self.project.path.conf.pyterraform(), ex)
            sys.exit(const.RC_KO)

    #@property
    #def plugin_cache_dir(self):
    #    """Where to cache tf plugins"""
    #    if not self._get('plugin_cache_dir'):
    #        self._set('plugin_cache_dir',
    #                  self.src.args.get('plugin_cache_dir') or \
    #                  self.src.environment.get('TF_plugin_cache_dir') or \
    #                  self.src.ftf.get('plugin_cache_dir'))
    #    return self._get('plugin_cache_dir')


class Stack(Setups):
    """Setting of a single stack"""
    def load_data(self):
        """Load data from state and conf, interpolate with args"""
        config = self._load_config()
        self._data = config

    @property
    def validation_schema(self):
        """Validate schema structure"""
        return Schema( \
        {
            #Optional('state_configuration_name'): str,
            #Optional('aws'): {
            #    'general': {
            #        'account': str,
            #        'region': str
            #    },
            #    'credentials': {
            #        'profile': str,
            #    }},
            Optional('vars'): {str: str},
            Optional('var-file'): str,
            Optional('terraform'): {
                Optional('custom-providers'): {str: Or(str, {'version': str, 'extension': str})}}
        })


    def _load_config(self):
        """Read stack configuration file, merged with element implicit into the cwd"""
        try:
            with self.project.path.stack.config().open() as _f:
                stack_config = yaml.safe_load(_f)
        except FileNotFoundError:
            logger.warning("No stack configuration found!")
            stack_config = dict()
        try:
            stack_config = self.validation_schema.validate(stack_config)
            stack_config.update(self.project.input.path)
            return stack_config
        except SchemaError as ex:
            logger.error('Configuration error in %s : %s',
                         self.project.path.stack.config(), ex)
            sys.exit(const.RC_KO)

    @property
    def backend_setup(self):
        """Option for backend setup"""
        params = list()
        for key, value in \
                self.project.cfg.pyt.get('state.backend', {}).get('s3', {}).items():
            value = value.format(**self.data)
            params.extend(['-backend-config', f"{key}={value}"])
            #params.append(f'-backend-config="{key}={value}"')
        return params
