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

import time

from concurrent import futures
from oslo_log import log as logging

from ironic_oneviewd.conf import CONF
from ironic_oneviewd import utils

LOG = logging.getLogger(__name__)

ENROLL_PROVISION_STATE = 'enroll'
MANAGEABLE_PROVISION_STATE = 'manageable'
INSPECTION_FAILED_PROVISION_STATE = 'inspect failed'
IN_USE_BY_ONEVIEW = 'is already in use by OneView.'

ACTION_STATES = [ENROLL_PROVISION_STATE,
                 MANAGEABLE_PROVISION_STATE,
                 INSPECTION_FAILED_PROVISION_STATE]


class NodeManager(object):
    def __init__(self, facade):
        self.facade = facade
        self.max_workers = CONF.DEFAULT.rpc_thread_pool_size
        self.executor = futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        )

    def run(self):
        retry_interval = CONF.DEFAULT.retry_interval

        while True:
            ironic_nodes = self.facade.get_ironic_node_list()
            provide_nodes = [node for node in ironic_nodes
                             if node.driver in utils.SUPPORTED_DRIVERS
                             if node.maintenance is False
                             if node.provision_state in ACTION_STATES]
            if provide_nodes:
                LOG.info("%(nodes)s Ironic nodes has been taken." %
                         {"nodes": len(provide_nodes)})
                self.executor.map(
                    self.manage_node_provision_state, provide_nodes)
            else:
                LOG.info("No Ironic nodes to manage.")

            time.sleep(retry_interval)

    def manage_node_provision_state(self, node):
        if node.provision_state == ENROLL_PROVISION_STATE:
            self.take_enroll_state_actions(node)
        elif node.provision_state == MANAGEABLE_PROVISION_STATE:
            self.take_manageable_state_actions(node)
        elif node.provision_state == INSPECTION_FAILED_PROVISION_STATE:
            self.take_inspect_failed_state_actions(node)

    def take_enroll_state_actions(self, node):
        LOG.info("Taking enroll state actions for node %(node)s." %
                 {'node': node.uuid})
        try:
            self.facade.set_node_provision_state(node, 'manage')
        except Exception as exc:
            LOG.error(exc.message)

    def take_manageable_state_actions(self, node):
        LOG.info("Taking manageable state actions for node %(node)s." %
                 {'node': node.uuid})
        try:
            if (CONF.openstack.inspection_enabled and
                    not utils.node_has_hardware_propeties(node)):
                self.facade.set_node_provision_state(node, 'inspect')
                return
            elif not (CONF.openstack.inspection_enabled or
                      utils.node_has_hardware_propeties(node)):
                LOG.warning("Node %(node)s has missing hardware properties "
                            "and Inspection is not enabled." % {
                                'node': node.uuid})
            self.facade.set_node_provision_state(node, 'provide')
        except Exception as e:
            LOG.error(e.message)

    def take_inspect_failed_state_actions(self, node):
        try:
            if node.last_error and IN_USE_BY_ONEVIEW in node.last_error:
                LOG.info("Inspection failed on node %(node)s due to machine "
                         "being in use by OneView. Moving it back to "
                         "manageable state." % {'node': node.uuid})
                self.facade.set_node_provision_state(node, 'manage')
            else:
                LOG.warning("Inspection failed on node %(node)s." %
                            {'node': node.uuid})
        except Exception as e:
            LOG.error(e.message)
