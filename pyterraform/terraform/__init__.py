"""All terraform commands, with proper context."""
import os
from copy import deepcopy
import subprocess
import shutil

from ..logs import logger
from . import binaries


class Command:
    """Terraform command executor"""

    def __init__(self, project):
        """
        :param project.Project project: the project on which the commands shall be run"""
        self.project = project
        self.utils = binaries.Utils(project)

    @property
    def _tf_bin(self):
        """Terraform binary path"""
        if not self.project.path.terraform.is_file():
            self.utils.tf_align_version('0.12.21')
        return self.project.path.terraform
        #if self.project.path.terraform.is_file():
        #    return self.project.path.terraform
        #if shutil.which("terraform") is not None:
        #    return shutil.which("terraform")
        # else install it

    def update_tf_version(self, version):
        """Update terraform to the wanted version"""
        self.utils.tf_align_version(version)

    def check_tf_version(self):
        """Check tf version and install"""
        if self.project.cfg.stack.get("terraform_version"):
            self.update_tf_version(self.project.cfg.stack["terraform_version"])

    def update_tf_providers(self):
        """Locally install tf providers"""
        # do we need a custom provider ?
        for provider, _config in self.project.cfg.stack.get('custom-providers', {}).items():
            if isinstance(_config, str):
                # This should be the version
                binaries.download_custom_provider(provider, _config)
            else:
                # _config should be a hash of version / extension
                binaries.download_custom_provider(
                    provider, _config['version'], _config['extension'])

    ########################
    ##  TF WRAPPING       ##
    ########################

    def version(self, wrapper_config=None):
        """Terraform version wrapper function."""
        return self._run_terraform('version', wrapper_config)

    def init(self, wrapper_config=None):
        """Terraform init wrapper function."""
        params = ['-input=false',
                  '-force-copy',
                  '-lock=true',
                  '-upgrade=true',
                  '-verify-plugins=true']
        if self.project.cfg.merged_variables.get('backend', {}).get('s3', {}):
            params.append('-backend=true')
        for key, value in \
                self.project.cfg.merged_variables.get('backend', {}).get('s3', {}).items():
            value = value.format(**self.project.cfg.merged_variables)
            params.append(f'-backend-config={key}={value}')
        return self._run_terraform('init', params)

    def _run_terraform(self, action, tf_params=None):
        """Run Terraform command."""
        if not tf_params:
            tf_params = self.project.cfg.cli_args.get('tf_params')

        # support for custom parameters
        command = [self._tf_bin, action]
        if tf_params is not None:
            if tf_params and tf_params[0] == '--':
                tf_params = tf_params[1:]
            command += tf_params

        cmd_env = deepcopy(os.environ)
        cmd_env['PATH'] = "{path}{sep}{old_path}".format(
            path=os.path.dirname(__file__), sep=os.pathsep, old_path=cmd_env.get('PATH', ''))

        pipe_plan_command = self.project.cfg.tf.get('pipe_plan_command')
        #pipe_plan = action == "plan" and wrapper_config.get('pipe_plan') and pipe_plan_command
        pipe_plan = action == "plan" and self.project.cfg.tf.get('pipe_plan') and pipe_plan_command
        stdout = subprocess.PIPE if pipe_plan else None
        with subprocess.Popen(command, cwd=self.project.path.stack, env=cmd_env,
                              shell=False, stdout=stdout) as process:
            logger.debug('Execute command "%s"', command)
            if pipe_plan:
                logger.debug('Piping command "%s"', pipe_plan_command)
                with subprocess.Popen(pipe_plan_command, cwd=self.project.path.stack, env=cmd_env,
                                      shell=True, stdin=process.stdout) as pipe_process:
                    try:
                        pipe_process.communicate()
                    except KeyboardInterrupt:
                        logger.warning('Received Ctrl+C')
                    except:  # noqa
                        pipe_process.kill()
                        pipe_process.wait()
                        raise
                    pipe_process.poll()
            try:
                process.communicate()
            except KeyboardInterrupt:
                logger.warning('Received Ctrl+C')
            except:  # noqa
                process.kill()
                process.wait()
                raise
            return process.poll()

    def run(self):
        """Execute the command asked for by the cli input"""
        action = getattr(self, self.project.cfg.cli_args.get('subcommand'))
        if not action:
            return self._run_terraform(self.project.cfg.cli_args.get('subcommand'))
            #return self._run_terraform(self.project.cfg.cli_args.get('subcommand'), wrapper_config)
        logger.info("Going to run command '%s'", self.project.cfg.cli_args.get('func'))
        return action()


#def terraform_apply(wrapper_config):
#    """Terraform apply wrapper function."""
#    always_trigger_init = wrapper_config['config'].get('always_trigger_init', False)
#    logger.debug("Checking 'always_trigger_init' option: {}".format(always_trigger_init))
#    if always_trigger_init:
#        logger.info('Init has been activated in config')
#        terraform_init(wrapper_config)
#
#    # do not force plan if unsafe
#    if wrapper_config['unsafe']:
#        return run_terraform('apply', wrapper_config)
#    else:
#        # plan config
#        plan_path = '{}/.run/plan_{}'.format(wrapper_config['rootdir'],
#            ''.join(random.choice(string.ascii_letters) for x in range(10)))
#        plan_wrapper_config = deepcopy(wrapper_config)
#        plan_wrapper_config['tf_params'][1:1] = ['-out', plan_path]
#        plan_return_code = run_terraform('plan', plan_wrapper_config)
#
#        # return Terraform return code if plan fails
#        if plan_return_code > 0:
#            return plan_return_code
#
#        # ask for confirmation
#        colored_account = colored(plan_wrapper_config['account'], 'yellow')
#        colored_environment = colored(plan_wrapper_config['environment'], 'red')
#        colored_region = colored(plan_wrapper_config['region'], 'blue')
#        colored_stack = colored(plan_wrapper_config['stack'], 'green')
#
#        if plan_wrapper_config['environment'] == 'global':
#            env_msg = '''
#    Account : {}
#Environment : {}
#      Stack : {}
#'''.format(colored_account, colored_environment, colored_stack)
#        else:
#            env_msg = '''
#    Account : {}
#Environment : {}
#     Region : {}
#      Stack : {}
#'''.format(colored_account, colored_environment, colored_region, colored_stack)
#
#        print('\nDo you really want to apply this plan on the following stack ?\n',
#              env_msg)
#        apply_input = input("'yes' to confirm: ")
#
#        try:
#            if apply_input == 'yes':
#                # apply config
#                apply_wrapper_config = deepcopy(wrapper_config)
#                apply_wrapper_config['tf_params'].append(plan_path)
#                apply_return_code = run_terraform('apply', apply_wrapper_config)
#
#                return apply_return_code
#            else:
#                logger.warning('Aborting apply.')
#        finally:
#            # delete plan
#            os.remove(plan_path)
#
#
#def terraform_console(wrapper_config):
#    """Terraform console wrapper function."""
#    return run_terraform('console', wrapper_config)
#
#
#def terraform_destroy(wrapper_config):
#    """Terraform destroy wrapper function."""
#    return run_terraform('destroy', wrapper_config)
#
#
#def terraform_fmt(wrapper_config):
#    """Terraform fmt wrapper function."""
#    return run_terraform('fmt', wrapper_config)
#
#
#def terraform_force_unlock(wrapper_config):
#    """Terraform force-unlock wrapper function."""
#    return run_terraform('force-unlock', wrapper_config)
#
#
#def terraform_get(wrapper_config):
#    """Terraform get wrapper function."""
#    # force update
#    if not any('-update' in x for x in wrapper_config['tf_params']):
#        wrapper_config['tf_params'][1:1] = ['-update']
#
#    # call subcommand
#    return run_terraform('get', wrapper_config)
#
#
#def terraform_graph(wrapper_config):
#    """Terraform graph wrapper function."""
#    return run_terraform('graph', wrapper_config)
#
#
#def terraform_import(wrapper_config):
#    """Terraform import wrapper function."""
#    return run_terraform('import', wrapper_config)
#
#
#def terraform_output(wrapper_config):
#    """Terraform output wrapper function."""
#    return run_terraform('output', wrapper_config)
#
#
#def terraform_plan(wrapper_config):
#    """Terraform plan wrapper function."""
#    always_trigger_init = wrapper_config['config'].get('always_trigger_init', False)
#    logger.debug("Checking 'always_trigger_init' option: {}".format(always_trigger_init))
#    if always_trigger_init:
#        logger.info('Init has been activated in config')
#        terraform_init(wrapper_config)
#    return run_terraform('plan', wrapper_config)
#
#
#def terraform_providers(wrapper_config):
#    """Terraform providers wrapper function."""
#    return run_terraform('providers', wrapper_config)
#
#
#def terraform_refresh(wrapper_config):
#    """Terraform refresh wrapper function."""
#    return run_terraform('refresh', wrapper_config)
#
#
#def terraform_show(wrapper_config):
#    """Terraform show wrapper function."""
#    return run_terraform('show', wrapper_config)
#
#
#def terraform_state(wrapper_config):
#    """Terraform state wrapper function."""
#    return run_terraform('state', wrapper_config)
#
#
#def terraform_taint(wrapper_config):
#    """Terraform taint wrapper function."""
#    return run_terraform('taint', wrapper_config)
#
#
#def terraform_untaint(wrapper_config):
#    """Terraform untaint wrapper function."""
#    return run_terraform('untaint', wrapper_config)
#
#
#def terraform_validate(wrapper_config):
#    """Terraform validate wrapper function."""
#    return run_terraform('validate', wrapper_config)
