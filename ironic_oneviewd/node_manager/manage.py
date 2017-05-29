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

import six

from concurrent import futures
from oslo_log import log as logging

from ironic_oneviewd.conf import CONF
from ironic_oneviewd import exceptions
from ironic_oneviewd import facade
from ironic_oneviewd import utils

LOG = logging.getLogger(__name__)

ENROLL_PROVISION_STATE = 'enroll'
MANAGEABLE_PROVISION_STATE = 'manageable'
AVAILABLE_PROVISION_STATE = 'available'
INSPECTION_FAILED_PROVISION_STATE = 'inspect failed'
ONEVIEW_PROFILE_APPLIED = 'ProfileApplied'
IN_USE_BY_ONEVIEW = 'is already in use by OneView.'

SUPPORTED_DRIVERS = [
    'agent_pxe_oneview',
    'iscsi_pxe_oneview',
    'fake_oneview'
]

ACTION_STATES = [ENROLL_PROVISION_STATE,
                 MANAGEABLE_PROVISION_STATE,
                 INSPECTION_FAILED_PROVISION_STATE]


class NodeManager(object):
    def __init__(self):
        self.facade = facade.Facade()
        self.max_workers = CONF.DEFAULT.rpc_thread_pool_size
        self.executor = futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        )

    def pull_ironic_nodes(self):
        ironic_nodes = self.facade.get_ironic_node_list()

        nodes = [node for node in ironic_nodes
                 if node.driver in SUPPORTED_DRIVERS
                 if node.provision_state in ACTION_STATES
                 if node.maintenance is False]

        if nodes:
            LOG.info(
                "%(nodes)s Ironic nodes has been taken." %
                {"nodes": len(nodes)}
            )
            self.executor.map(self.manage_node_provision_state, nodes)

    def manage_node_provision_state(self, node):
        if node.provision_state == ENROLL_PROVISION_STATE:
            self.take_enroll_state_actions(node)
        elif node.provision_state == MANAGEABLE_PROVISION_STATE:
            self.take_manageable_state_actions(node)
        elif node.provision_state == INSPECTION_FAILED_PROVISION_STATE:
            self.take_inspect_failed_state_actions(node)

    def take_enroll_state_actions(self, node):
        LOG.info(
            "Taking enroll state actions for node %(node)s." %
            {'node': node.uuid}
        )

        try:
            self.apply_node_port_conf(node)
        except exceptions.NodeAlreadyHasPortForThisMacAddress as ex:
            LOG.warning(six.text_type(ex))
        except exceptions.NoBootableConnectionFoundException as ex:
            LOG.warning(six.text_type(ex))
            return

        try:
            self.facade.set_node_provision_state(node, 'manage')
        except Exception as e:
            LOG.error(e.message)

    def take_manageable_state_actions(self, node):
        LOG.info(
            "Taking manageable state actions for node %(node)s." %
            {'node': node.uuid}
        )

        if (CONF.openstack.inspection_enabled and
                not utils.node_has_hardware_propeties(node)):
            self.facade.set_node_provision_state(node, 'inspect')
            return
        elif not (CONF.openstack.inspection_enabled or
                  utils.node_has_hardware_propeties(node)):
            LOG.warning(
                "Node %(node)s has missing hardware properties and "
                "Inspection is not enabled." % {'node': node.uuid}
            )
        try:
            self.facade.set_node_provision_state(node, 'provide')
        except Exception as e:
            LOG.error(e.message)

    def take_inspect_failed_state_actions(self, node):
        if (node.last_error and (IN_USE_BY_ONEVIEW in node.last_error)):
            LOG.info(
                "Inspection failed on node %(node)s due to machine being in "
                "use by OneView. Moving it back to manageable state." %
                {'node': node.uuid}
            )

            self.facade.set_node_provision_state(node, 'manage')

        else:
            LOG.warning(
                "Inspection failed on node %(node)s." % {'node': node.uuid}
            )

    def apply_node_port_conf(self, node):
        node_info = utils.get_node_info_from_node(node)
        server_hardware = self.facade.get_server_hardware(node_info)

        try:
            mac = utils.get_server_hardware_mac(server_hardware)
        except exceptions.OneViewResourceNotFoundError as ex:
            LOG.warning(six.text_type(ex))
            console_url = self.facade.get_server_hardware_remote_console_url(
                node_info
            )
            mac = utils.get_server_hardware_mac_from_ilo(console_url)

        return self.get_a_port_to_apply_to_node(node, mac)

    def get_a_port_to_apply_to_node(self, node, mac):
        port_list_by_mac = self.facade.get_port_list_by_mac(mac)
        if not port_list_by_mac:
            return self.apply_port_to_node(node, mac)
        else:
            port_obj = self.facade.get_port(port_list_by_mac[0].uuid)
            if port_obj.node_uuid != node.uuid:
                return self.apply_port_to_node(node, mac)
            else:
                raise exceptions.NodeAlreadyHasPortForThisMacAddress(mac)

    def apply_port_to_node(self, node, mac):
        if node.driver_info.get('use_oneview_ml2_driver'):
            local_link_connection = self.set_local_link_connection(node, mac)
            return self.facade.create_node_port(
                node.uuid, mac, local_link_connection)
        return self.facade.create_node_port(node.uuid, mac)

    def set_local_link_connection(self, node, mac):
        local_link_connection = {}
        if node.driver_info.get('use_oneview_ml2_driver'):
            server_hardware_id = utils.server_hardware_uuid_from_node(node)
            switch_info = (
                '{"server_hardware_id": "%(server_hardware_id)s", '
                '"bootable": "%(bootable)s"}') % {
                    'server_hardware_id': server_hardware_id,
                    'bootable': True}
            local_link_connection = {
                "switch_id": "01:23:45:67:89:ab",
                "port_id": "",
                "switch_info": switch_info
            }
        return local_link_connection
