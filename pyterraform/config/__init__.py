"""Manage configuration options, getting metadata from filesystem,
current working directory and cli options"""
import os
import sys
from pathlib import Path
import copy

import yaml
from schema import Schema, Optional, Or, SchemaError
import deep_merge

from .. import constants as const
from ..logs import logger
from . import setup

TFWRAPPER_DEFAULT_CONFIG = {
    'always_trigger_init': False,
    'pipe_plan_command': 'cat',
    'tf_binary_cache': Path.home() / '.terraform' / 'binaries'}

STACK_CONFIGURATION_SCHEMA = Schema({
    Optional('state_configuration_name'): str,
    Optional('aws'): {
        'general': {
            'account': str,
            'region': str
        },
        'credentials': {
            'profile': str,
        }
    },
    Optional('terraform'): {
        Optional('vars'): {str: str},
        Optional('custom-providers'): {str: Or(str, {'version': str, 'extension': str})},
    },
})

STATE_CONFIGURATION_SCHEMA = Schema({
    Optional('profile'): str,
    Optional('region'): str,
    Optional('account'): str,
    Optional('assume_role'): str,
    Optional('backend'): {Optional('s3'): {
        'profile': str,
        'region': str,
        'bucket': str,
        'key': str,
        'dynamodb_table': str,
        'acl': str}}})


def overwrite_notnull(v1, v2, **kwargs):  # pylint: disable=invalid-name,unused-argument
    """
    Completely overwrites one value with another, if not None.
    """
    if v2 is None:
        return copy.deepcopy(v1)
    return copy.deepcopy(v2)


class Data:
    """Data configuration placeholder"""
    def __init__(self, cli_args: dict, config):
        self.config = config
        self._data = {'args': cli_args,
                      'path': None,
                      'env': dict(os.environ),
                      'file_state': None,
                      'file_stack': None,
                      'file_wrapper': None}

    @property
    def _prj(self):
        """Just a shortcut"""
        return self.config.project
    @property
    def args(self):
        """Store cli arguments"""
        return self._data['args']
    @property
    def path(self):
        """Infos from cwd"""
        if self._data['path'] is None:
            self._data['path'] = self._prj.path.get_stackinfo_from_cwd()
        return self._data['path']
    @property
    def environment(self):  # pylint: disable=invalid-name
        """Environment configuration"""
        return self._data['env']
    @property
    def ftf(self):  # pylint: disable=invalid-name
        """Wrapper configuration"""
        if self._data['file_wrapper'] is None:
            tmp = TFWRAPPER_DEFAULT_CONFIG
            if self._prj.path.conf_tfwrapper.is_file():
                with open(self._prj.path.conf_tfwrapper, 'r') as _f:
                    logger.debug("Loading wrapper config from '%s'",
                                 self._prj.path.conf_tfwrapper)
                    tmp.update(yaml.safe_load(_f))
                self._data['file_wrapper'] = tmp
            else:
                logger.info("No configuration stack file found under '%s'",
                            self._prj.path.conf_tfwrapper)
                self._data['file_wrapper'] = dict()
        return self._data['file_wrapper']
    @property
    def fstate(self):
        """State backend configuration"""
        if self._data['file_state'] is None:
            if not self._prj.path.conf_state.is_file():
                logger.warning("No state configuration file found!")
                self._data['file_state'] = dict()
            with open(self._prj.path.conf_state, 'r') as _f:
                logger.debug("Loading state config from '%s'", self._prj.path.conf_state)
                state_config = yaml.safe_load(_f)
            try:
                STATE_CONFIGURATION_SCHEMA.validate(state_config)
                self._data.state = state_config
            except SchemaError as ex:
                logger.error('Configuration error in %s : %s',
                             self._prj.path.conf_state, ex)
                sys.exit(const.RC_KO)
        return self._data['file_state']
    @property
    def fstack(self):
        """Stack custom parameters"""
        if self._data['file_stack'] is None:
            if not self._prj.path.stack_config.is_file():
                logger.warning("No stack configuration found!")
                self._data['file_stack'] = dict()
            with open(self._prj.path.stack_config, 'r') as _f:
                stack_config = yaml.safe_load(_f)
            try:
                STACK_CONFIGURATION_SCHEMA.validate(stack_config)
                self._data['file_stack'] = stack_config
            except SchemaError as ex:
                logger.error('Configuration error in %s : %s',
                             self._prj.path.stack_config, ex)
                sys.exit(const.RC_KO)
        return self._data['file_stack']


class Configuration:
    """Configuration metadata holder and interpolation.
    It will manage stack configuration, pyterraform wrapper options
    and environment variables, more..."""

    def __init__(self, project):
        self.project = project
        self.stack = setup.Stack(project)
        self.tfw = setup.Pyterraform(project)

    @property
    def _data(self):
        """Just for convenience"""
        return self.project.data

    #@property
    #def merged_variables(self):
    #    """Return all variables merged together.
    #    Order (by priority):
    #    - cli_args
    #    - path_info
    #    - os.environ
    #    - stack
    #    - state
    #    - tf_wrapper
    #    """
    #    mixin = dict()
    #    priority = [self.args, self.path, dict(os.environ), self.stack,
    #                self.state, self.tf]
    #    kpolicy = dict(merge_lists=overwrite_notnull, merge_ints=overwrite_notnull,
    #                   merge_floats=overwrite_notnull, merge_strings=overwrite_notnull,
    #                   merge_other=overwrite_notnull)
    #    deep_merge.merge(mixin, *reversed(priority), **kpolicy)
    #    return mixin

    def get_stack_variables(self):
        """Return dict of variable to pass to TF."""
        terraform_vars = self.stack.tf_vars
        terraform_vars['environment'] = self.stack.environment
        terraform_vars['stack'] = self.stack.stack
        # AWS variables
        terraform_vars['aws_access_key'] = self.project.session.access_key
        terraform_vars['aws_secret_key'] = self.project.session.secret_key
        terraform_vars['aws_token'] = self.project.session.token
        return terraform_vars

    def export_tf_vars(self):
        """Export TF vars to os environment"""
        for var, value in self.get_stack_variables().items():
            if value is not None:
                os.environ[f'TF_VAR_{var}'] = str(value)
