# -*- encoding: utf-8 -*-
#
# Copyright 2015 Hewlett-Packard Development Company, L.P.
# Copyright 2015 Universidade Federal de Campina Grande
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

import sys

from ironicclient.openstack.common import cliutils
from ironic_oneviewd.config import ConfClient
from ironic_oneviewd.commands.manage import NodeManager


def do_manage_ironic_nodes(args):
    """Show a list of OneView servers to be created as nodes in Ironic
    """
    if args.config_file is not "":
        config_file = args.config_file

    defaults = {
        "ca_file": "",
        "insecure": False,
        "tls_cacert_file": "",
        "allow_insecure_connections": False,
    }

    conf = ConfClient(config_file, defaults)
    node_manager = NodeManager(conf)
    while True:
        node_manager.pull_ironic_nodes()
