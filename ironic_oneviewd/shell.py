# Copyright (2015-2017) Hewlett Packard Enterprise Development LP
# Copyright (2015-2017) Universidade Federal de Campina Grande
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
"""Daemon to the Ironic OneView drivers."""

from __future__ import print_function
import sys

import argparse
import six

from oslo_log import log as logging
from oslo_utils import encodeutils

import ironic_oneviewd
from ironic_oneviewd.conf import CONF
from ironic_oneviewd import manage as oneviewd_manager
from ironic_oneviewd import utils

COMMAND_MODULES = [
    oneviewd_manager,
]


def get_base_parser():
    parser = argparse.ArgumentParser(
        prog='ironic-oneviewd',
        description=__doc__.strip(),
        epilog='See "ironic-oneviewd --help COMMAND" '
               'for help on a specific command.',
        add_help=False,
        formatter_class=HelpFormatter,
    )

    # Global arguments
    parser.add_argument('-h', '--help',
                        action='store_true',
                        help=argparse.SUPPRESS)

    parser.add_argument('--version',
                        action='version',
                        version=ironic_oneviewd.__version__)

    parser.add_argument('-c', '--config-file',
                        default='/etc/ironic-oneviewd/'
                                'ironic-oneviewd.conf',
                        help='Path to the Ironic OneView daemon '
                             'configuration file.')

    parser.add_argument('-l', '--log-file',
                        help='Path to the Ironic OneView daemon '
                             'logging file.')

    return parser


class IronicOneViewD(object):
    def __init__(self):
        self.subcommands = {}
        self.parser = None

    def get_subcommand_parser(self):
        parser = get_base_parser()
        subparsers = parser.add_subparsers(metavar='<subcommand>')
        enhance_parser(subparsers, self.subcommands)
        define_commands_from_module(subparsers, self, self.subcommands)
        return parser

    @utils.arg('command', metavar='<subcommand>', nargs='?',
               help='Display help for <subcommand>')
    def do_help(self, args):
        """Display help about this program or one of its subcommands."""
        if getattr(args, 'command', None):
            if args.command in self.subcommands:
                self.subcommands[args.command].print_help()
            else:
                raise Exception("'%s' is not a valid subcommand" %
                                args.command)
        else:
            self.parser.print_help()

    def main(self, argv):
        log_domain = "DEFAULT"
        parser = get_base_parser()
        (options, args) = parser.parse_known_args(argv)
        subcommand_parser = self.get_subcommand_parser()
        self.parser = subcommand_parser

        logging.register_options(CONF)
        CONF(default_config_files=[options.config_file])
        logging.setup(CONF, log_domain)

        if options.help:
            self.do_help(options)

        if 'help' not in argv:
            oneviewd_manager.do_oneview_daemon()

        args = subcommand_parser.parse_args(argv)

        # Short-circuit and deal with these node_manager right away.
        if args.func == self.do_help:
            self.do_help(args)
            return 0


def define_command(subparsers, command, callback, cmd_mapper):
    """Define a command in the subparsers collection.

    :param subparsers: subparsers collection where the command will go
    :param command: command name
    :param callback: function that will be used to process the command
    """
    desc = callback.__doc__ or ''
    daemon_help = desc.strip().split('\n')[0]
    arguments = getattr(callback, 'arguments', [])

    subparser = subparsers.add_parser(command, help=daemon_help,
                                      description=desc,
                                      add_help=False,
                                      formatter_class=HelpFormatter)
    subparser.add_argument('-h', '--help', action='help',
                           help=argparse.SUPPRESS)
    cmd_mapper[command] = subparser
    for (args, kwargs) in arguments:
        subparser.add_argument(*args, **kwargs)
    subparser.set_defaults(func=callback)


def define_commands_from_module(subparsers, command_module, cmd_mapper):
    """Add *do_* methods in a module and node_manager into a subparsers."""
    for method_name in (a for a in dir(command_module) if a.startswith('do_')):
        # Commands should be hypen-separated instead of underscores.
        command = method_name[3:].replace('_', '-')
        callback = getattr(command_module, method_name)
        define_command(subparsers, command, callback, cmd_mapper)


def enhance_parser(subparsers, cmd_mapper):
    for command_module in COMMAND_MODULES:
        define_commands_from_module(subparsers, command_module, cmd_mapper)


class HelpFormatter(argparse.HelpFormatter):
    def start_section(self, heading):
        # Title-case the headings
        heading = '%s%s' % (heading[0].upper(), heading[1:])
        super(HelpFormatter, self).start_section(heading)


def main():
    try:
        IronicOneViewD().main(sys.argv[1:])
    except KeyboardInterrupt:
        print("\nironic-oneviewd stopped", file=sys.stderr)
        sys.exit(130)
    except Exception as exc:
        print(encodeutils.safe_encode(six.text_type(exc)), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
