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

import retrying

from ironic_oneviewd.conf import CONF
from ironic_oneviewd.node_manager.manage import NodeManager
from ironic_oneviewd import service_logging as logging

LOG = logging.getLogger(__name__)


def do_manage_ironic_nodes(args):
    """Show a list of OneView servers to be created as nodes in Ironic."""
    if args.log_file:
        logging.redefine_logfile_handlers(args.log_file)
    if args.config_file:
        CONF(default_config_files=[args.config_file])

    node_manager = NodeManager()
    retry_interval_in_ms = CONF.DEFAULT.retry_interval * 1000

    @retrying.retry(wait_fixed=retry_interval_in_ms)
    def execute():
        try:
            node_manager.pull_ironic_nodes()
        except Exception as ex:
            LOG.error(ex.message)
        raise Exception("Continue trying...")
    execute()
