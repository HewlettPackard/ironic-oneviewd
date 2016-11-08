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
import traceback

from concurrent import futures
from oslo_log import log as logging

from ironic_oneviewd.conf import CONF
from ironic_oneviewd import exceptions
from ironic_oneviewd import facade
from ironic_oneviewd import utils

LOG = logging.getLogger(__name__)

ENROLL_PROVISION_STATE = 'enroll'
MANAGEABLE_PROVISION_STATE = 'manageable'
ONEVIEW_PROFILE_APPLIED = 'ProfileApplied'

SUPPORTED_DRIVERS = [
    'agent_pxe_oneview',
    'iscsi_pxe_oneview',
    'fake_oneview'
]


class NodeManager(object):

    def __init__(self):
        self.facade = facade.Facade()
        self.max_workers = CONF.DEFAULT.rpc_thread_pool_size
        self.executor = futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        )

    def pull_ironic_nodes(self):
        ironic_nodes = self.facade.get_ironic_node_list()

        LOG.info(
            "%(nodes)s Ironic nodes has been taken." %
            {"nodes": len(ironic_nodes)}
        )

        nodes = [node for node in ironic_nodes
                 if node.driver in SUPPORTED_DRIVERS
                 if node.maintenance is False]

        self.executor.map(self.manage_node_provision_state, nodes)

    def manage_node_provision_state(self, node):
        if node.provision_state == ENROLL_PROVISION_STATE:
            self.take_enroll_state_actions(node)
        elif node.provision_state == MANAGEABLE_PROVISION_STATE:
            self.take_manageable_state_actions(node)

    def take_enroll_state_actions(self, node):
        LOG.info(
            "Taking enroll state actions for node %(node)s." %
            {'node': node.uuid}
        )

        if not utils.dynamic_allocation_enabled(node):
            try:
                self.apply_server_profile(
                    node
                )
            except (
                exceptions.NodeAlreadyHasServerProfileAssignedException
            ) as ex:
                LOG.warning(six.text_type(ex))
            except exceptions.ServerProfileApplicationException as ex:
                LOG.warning(six.text_type(ex))
                return

            try:
                self.apply_node_port_configuration(
                    node
                )
            except exceptions.NodeAlreadyHasPortForThisMacAddress as ex:
                LOG.warning(six.text_type(ex))
            except exceptions.NoBootableConnectionFoundException as ex:
                LOG.warning(six.text_type(ex))
                return
        else:
            try:
                self.apply_node_port_conf_for_dynamic_allocation(
                    node
                )
            except exceptions.NodeAlreadyHasPortForThisMacAddress as ex:
                LOG.warning(six.text_type(ex))
            except exceptions.NoBootableConnectionFoundException as ex:
                LOG.warning(six.text_type(ex))
                return

        try:
            self.facade.set_node_provision_state(node, 'manage')
        except Exception:
            LOG.error(traceback.format_exc())
            return

    def take_manageable_state_actions(self, node):
        LOG.info(
            "Taking manageable state actions for node %(node)s." %
            {'node': node.uuid}
        )

        try:
            self.facade.set_node_provision_state(node, 'provide')
        except Exception:
            LOG.error(traceback.format_exc())

    def server_hardware_has_server_profile_fully_applied(self, node):
        server_hardware_uuid = utils.server_hardware_uuid_from_node(node)
        server_hardware_state = self.facade.get_server_hardware_state(
            server_hardware_uuid
        )
        return server_hardware_state == ONEVIEW_PROFILE_APPLIED

    def server_hardware_has_server_profile_applied(self, node):
        server_hardware_uri = utils.server_hardware_uri_from_node(
            node
        )
        profile_applied = (
            self.facade.is_server_profile_applied_on_server_hardware(
                server_hardware_uri
            )
        )
        return profile_applied

    def apply_server_profile(self, node):
        server_profile_uri = self.server_profile_uri_from_node(
            node
        )

        node_info = utils.get_node_info_from_node(node)

        server_profile_name = "Ironic [%s]" % (node.uuid)

        if server_profile_uri is None:
            try:
                server_profile_uri = (
                    self.facade.generate_and_assign_sp_from_spt(
                        server_profile_name,
                        node_info
                    )
                )
            except Exception:
                raise exceptions.ServerProfileApplicationException(node)
        else:
            raise exceptions.NodeAlreadyHasServerProfileAssignedException(
                node,
                server_profile_uri
            )

    def apply_node_port_configuration(self, node):
        if not self.server_hardware_has_server_profile_fully_applied(node):
            LOG.error(
                "The Server Profile application is not "
                "finished yet for node %(node)s." %
                {'node': node.uuid}
            )
            return

        node_info = utils.get_node_info_from_node(node)

        assigned_server_profile_uri = self.server_profile_uri_from_node(
            node
        )
        server_profile = self.facade.get_server_profile_assigned_to_sh(
            node_info
        )
        primary_boot_connection = None

        if server_profile.connections:
            for connection in server_profile.connections:
                boot = connection.get('boot')
                if (boot is not None and
                   boot.get('priority').lower() == 'primary'):
                    primary_boot_connection = connection

            if primary_boot_connection is None:
                raise exceptions.NoBootableConnectionFoundException(
                    assigned_server_profile_uri
                )
            mac = primary_boot_connection.get('mac')
        else:
            server_hardware_uuid = utils.server_hardware_uuid_from_node(node)
            mac = self.facade.get_server_hardware_mac(server_hardware_uuid)

        return self.get_a_port_to_apply_to_node(node, mac)

    def apply_node_port_conf_for_dynamic_allocation(self, node):
        server_hardware_uuid = utils.server_hardware_uuid_from_node(node)
        mac = self.facade.get_server_hardware_mac(server_hardware_uuid)

        return self.get_a_port_to_apply_to_node(node, mac)

    def server_profile_uri_from_node(self, node):
        node_info = utils.get_node_info_from_node(node)
        server_profile_uri = None
        try:
            server_profile = self.facade.get_server_profile_assigned_to_sh(
                node_info
            )

            if node.uuid in server_profile.name:
                return server_profile.uri
            else:
                return server_profile_uri

        except Exception:
            return server_profile_uri

    def get_a_port_to_apply_to_node(self, node, mac):
        port_list_by_mac = self.facade.get_port_list_by_mac(mac)

        if not port_list_by_mac:
            return self.facade.create_node_port(node.uuid, mac)
        else:
            port_obj = self.facade.get_port(port_list_by_mac[0].uuid)
            if port_obj.node_uuid != node.uuid:
                return self.facade.create_node_port(
                    node.uuid, mac
                )
            else:
                raise exceptions.NodeAlreadyHasPortForThisMacAddress(
                    mac
                )
