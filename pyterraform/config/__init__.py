"""Manage configuration options, getting metadata from filesystem,
current working directory and cli options"""
import os
import sys
import copy

from . import setup


def overwrite_notnull(v1, v2, **kwargs):  # pylint: disable=invalid-name,unused-argument
    """
    Completely overwrites one value with another, if not None.
    """
    if v2 is None:
        return copy.deepcopy(v1)
    return copy.deepcopy(v2)


class Configuration:
    """Configuration metadata holder and parameters interpolation.
    It will manage stack configuration, pyterraform wrapper options
    and environment variables, more..."""

    def __init__(self, project):
        self.project = project
        self.stack = setup.Stack(project)
        self.pyterraform = setup.Pyterraform(project)

    @property
    def pyt(self):
        """Alias to pyterraform"""
        return self.pyterraform

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

    #@staticmethod
    #def infec
    def get_tf_env(self):
        """Environment option for terraform"""
        envs = dict()
        cli_args = list()
        if self.pyt.get('config.tf_data_dir'):
            envs['TF_DATA_DIR'] = self.pyt.get('config.tf_data_dir').format(**self.stack.data)
        if self.pyt.get('config.tf_plugin_dir'):
            cli_args.append(f"-plugin-dir={self.pyt.get('config.tf_plugin_dir')}")
        if cli_args:
            envs['TF_CLI_ARGS'] = ' '.join(cli_args)
        for var, value in envs.items():
            if value is not None:
                os.environ[var] = str(value)

    def get_stack_custom_env(self):
        """Custom runtime env. Is it needed?"""
        terraform_vars = dict()
        terraform_vars['environment'] = self.stack.get("environment")
        terraform_vars['stack'] = self.stack.get("stack")
        # AWS variables
        terraform_vars['aws_access_key'] = self.project.session.access_key
        terraform_vars['aws_secret_key'] = self.project.session.secret_key
        terraform_vars['aws_token'] = self.project.session.token
        return terraform_vars

    def get_stack_tfvariables(self):
        """Return dict of variable to be passed to TF as environment."""
        tf_vars = dict()
        for key, value in self.stack.get("vars", dict()).items():
            if value in [None, ""]:
                continue
            tf_vars[f'TF_VAR_{key}'] = value
        return tf_vars

    def get_stack_varfile(self):
        """Return the variable file to be passed to TF"""
        vfile = self.stack.get('var-file')
        if vfile:
            return f'-var-file={vfile}'
        return ''

    def context_for(self, command):
        """Extract the proper execution contest for the given command.
        :return: cli arguments definition and environment
        :rtype: list(str), dict"""
        #TF_IN_AUTOMATION input=False
        cli_args = list()
        envs = copy.deepcopy(self.project.input.environment)
        if self.pyt.get('config.tf_data_dir'):
            envs['TF_DATA_DIR'] = self.pyt.get('config.tf_data_dir').format(**self.stack.data)
        #if self.pyt.get('config.tf_plugin_dir'):
        #    cli_args.append(f"-plugin-dir={self.pyt.get('config.tf_plugin_dir')}")
        if command == 'console':
            envs.update(self.get_stack_tfvariables())
            cli_args = ' '.join(self.get_stack_varfile())
        return cli_args, envs
