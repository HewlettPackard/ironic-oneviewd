# Copyright 2017 Hewlett Packard Enterprise Development LP
# Copyright 2017 Universidade Federal de Campina Grande
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

from multiprocessing import Process
from oslo_log import log as logging

from ironic_oneviewd.facade import Facade
from ironic_oneviewd.inventory_manager.manage import InventoryManager
from ironic_oneviewd.node_manager.manage import NodeManager

LOG = logging.getLogger(__name__)


def do_oneview_daemon():
    """Ironic OneView Daemon."""
    LOG.info('Starting OneView Daemon')

    facade = Facade()
    node_manager = NodeManager(facade)
    inventory_manager = InventoryManager(facade)

    def execute():
        p1 = Process(target=node_manager.run)
        p1.start()

        p2 = Process(target=inventory_manager.run)
        p2.start()

        p1.join()
        p2.join()

    execute()
