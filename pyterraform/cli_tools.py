"""Parser for cli inputs"""
import sys
import argparse
from . import constants as const


def parse_args(project, args):  # pylint: disable=too-many-locals,too-many-statements
    """Parse command line arguments."""
    # pylint: disable=unused-variable
    # terraform params doc
    tf_params_help = 'Any Terraform parameters after a "--" delimiter'

    # argparse
    parser = argparse.ArgumentParser(prog="pyterraform",
                                     description='Terraform wrapper.')
    parser.add_argument("-d", "--debug",
                        action='store_true', default=False,
                        help="Enable debug output.")
    parser.add_argument(
        '-c', '--confdir',
        help='Configuration directory. Used to detect the project root. Defaults to conf.',
        default='conf')
    for stack_element in project.cfg.pyt.stack_folder_structure:  # at least stack and environment
        parser.add_argument(f'--{stack_element}',
                            help='Target stack definition. Autodetected if none is provided.',
                            nargs='?')
    #parser.add_argument('-a', '--account',
    #                    help='Target account. Autodetected if none is provided.',
    #                    nargs='?')
    #parser.add_argument('-r', '--region',
    #                    help='Target region. Autodetected if none is provided.',
    #                    nargs='?')
    #parser.add_argument('--profile',
    #                    help='Target profile. Autodetected if none is provided.',
    #                    nargs='?')
    parser.add_argument('--log-to-file', help='Enable logging to local file.',
                        action='store_true', default=False)
    parser.add_argument('--unattended', help='For automatic run (like CI).',
                        action='store_true', default=False)
    parser.add_argument('-p', '--plugin-cache-dir', help='Plugins cache directory.',
                        default=f'{const.HOME_DIR}/.terraform.d/plugin-cache')

    subparsers = parser.add_subparsers(dest='subcommand',
                                       help='terraform subcommands plus some pyterraform gotchas')

    subparsers.add_parser('list_modules', help='List modules used by terraform')
    subparsers.add_parser('list_providers',
                          help='List providers declared into terraform stack')
    subparsers.add_parser('local_install', help='Install dependencies required by terraform')
    parser_apply = subparsers.add_parser('apply', help='terraform apply')
    #parser_apply.add_argument('-u', '--unsafe',
    #                          help='Do not force plan and human interaction before apply.',
    #                          action='store_true', default=False)
    #parser_apply.add_argument("-l", "--pipe-plan",
    #                          action='store_true', default=False,
    #                          help=("Pipe plan output to the command set in config"
    #                          " or passed in --pipe-plan-command argument (cat by default)."))
    #parser_apply.add_argument("--pipe-plan-command",
    #                          action='store', nargs='?',
    #          help="Pipe plan output to the command of your choice set as argument inline value.")
    parser_apply.add_argument('tf_params', nargs=argparse.REMAINDER, help=tf_params_help)

    parser_console = subparsers.add_parser('console', help='terraform console')
    parser_console.add_argument('tf_params', nargs=argparse.REMAINDER, help=tf_params_help)

    #parser_destroy = subparsers.add_parser('destroy', help='terraform destroy')
    #parser_destroy.add_argument('tf_params', nargs=argparse.REMAINDER, help=tf_params_help)

    parser_fmt = subparsers.add_parser('fmt', help='terraform fmt')
    parser_fmt.add_argument('tf_params', nargs=argparse.REMAINDER, help=tf_params_help)

    parser_force_unlock = subparsers.add_parser('force-unlock', help='terraform force-unlock')
    parser_force_unlock.add_argument('tf_params', nargs=argparse.REMAINDER, help=tf_params_help)

    parser_get = subparsers.add_parser('get', help='terraform get')
    parser_get.add_argument('tf_params', nargs=argparse.REMAINDER, help=tf_params_help)

    #parser_graph = subparsers.add_parser('graph', help='terraform graph')
    #parser_graph.add_argument('tf_params', nargs=argparse.REMAINDER, help=tf_params_help)

    parser_import = subparsers.add_parser('import', help='terraform import')
    parser_import.add_argument('tf_params', nargs=argparse.REMAINDER, help=tf_params_help)

    parser_init = subparsers.add_parser('init', help='terraform init')
    parser_init.add_argument('tf_params', nargs=argparse.REMAINDER, help=tf_params_help)

    parser_output = subparsers.add_parser('output', help='terraform output')
    parser_output.add_argument('tf_params', nargs=argparse.REMAINDER, help=tf_params_help)

    parser_plan = subparsers.add_parser('plan', help='terraform plan')
    parser_plan.add_argument("-l", "--pipe-plan",
                             action='store_true', default=False,
                             help=("Pipe plan output to the command set in config"
                                   " or passed in --pipe-plan-command argument (cat by default)."))
    #parser_plan.add_argument("--pipe-plan-command",
    #                         action='store', nargs='?',
    #          help="Pipe plan output to the command of your choice set as argument inline value.")
    parser_plan.add_argument('tf_params', nargs=argparse.REMAINDER, help=tf_params_help)

    parser_providers = subparsers.add_parser('providers', help='terraform providers')
    parser_providers.add_argument('tf_params', nargs=argparse.REMAINDER, help=tf_params_help)

    parser_refresh = subparsers.add_parser('refresh', help='terraform refresh')
    parser_refresh.add_argument('tf_params', nargs=argparse.REMAINDER, help=tf_params_help)

    parser_show = subparsers.add_parser('show', help='terraform show')
    parser_show.add_argument('tf_params', nargs=argparse.REMAINDER, help=tf_params_help)

    parser_state = subparsers.add_parser('state', help='terraform state')
    parser_state.add_argument('tf_params', nargs=argparse.REMAINDER, help=tf_params_help)

    parser_taint = subparsers.add_parser('taint', help='terraform taint')
    parser_taint.add_argument('tf_params', nargs=argparse.REMAINDER, help=tf_params_help)

    parser_untaint = subparsers.add_parser('untaint', help='terraform untaint')
    parser_untaint.add_argument('tf_params', nargs=argparse.REMAINDER, help=tf_params_help)

    parser_validate = subparsers.add_parser('validate', help='terraform validate')
    parser_validate.add_argument('tf_params', nargs=argparse.REMAINDER, help=tf_params_help)

    parser_version = subparsers.add_parser('version', help='terraform version')
    parser_version.add_argument('tf_params', nargs=argparse.REMAINDER, help=tf_params_help)

    #parser_bootstrap = subparsers.add_parser('bootstrap', help='bootstrap configuration')
    #parser_bootstrap.add_argument('template', nargs='?',
    #        help='template to use during bootstrap', default=None)

    #parser_foreach = subparsers.add_parser('foreach', help='execute command for each stack')
    #parser_foreach.add_argument('-c', dest='shell', action="store_true",
    #          help='execute command in a shell')
    #parser_foreach.add_argument('command', nargs=argparse.REMAINDER,
    #          help='command to execute after a "--" delimiter')

    #parser_switchver = subparsers.add_parser('switchver', help='switch terraform version')
    #parser_switchver.add_argument('version', nargs=1, help='terraform version to use')

    parsed_args = parser.parse_args(args)

    if getattr(parsed_args, 'subcommand') is None:
        parser.print_help(file=sys.stderr)
        raise SystemExit(0)

    #if parsed_args.func == foreach:
    #    if len(parsed_args.command) > 0 and parsed_args.command[0] == '--':
    #        parsed_args.command = parsed_args.command[1:]
    #    if len(parsed_args.command) < 1:
    #        raise ValueError("foreach: error: a command is required")
    #    if parsed_args.shell and len(parsed_args.command) > 1:
    #raise ValueError("foreach: error: -c must be followed by a single argument (hint: use quotes)")
    #    parsed_args.executable = os.environ.get("SHELL", None) if parsed_args.shell else None

    return parsed_args
