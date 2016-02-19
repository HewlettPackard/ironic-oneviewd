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

import six

from concurrent import futures

from ironic_oneviewd import facade
from ironic_oneviewd import service_logging as logging
from ironic_oneviewd import sync_exceptions as exceptions
from ironic_oneviewd.openstack.common._i18n import _


LOG = logging.getLogger(__name__)


ENROLL_PROVISION_STATE = 'enroll'
MANAGEABLE_PROVISION_STATE = 'manageable'

SUPPORTED_DRIVERS = ["agent_pxe_oneview",
                     "iscsi_pxe_oneview",
                     "fake_oneview"]


class NodeManager:

    def __init__(self, conf_client):

        self.conf_client = conf_client
        self.facade = facade.Facade(conf_client)
        self.max_workers = int(
            self.conf_client.DEFAULT.rpc_thread_pool_size
        )
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

        try:
            self.apply_server_profile(
                node
            )
        except exceptions.ServerHardwareAlreadyHasServerProfileException as ex:
            LOG.error(ex.message)
            applied = self.server_hardware_has_server_profile_applied(node)
            LOG.info("Has server profile applied %s" % applied)
            if not applied:
                return

        try:
            self.apply_node_port_configuration(
                node
            )
        except exceptions.NoBootableConnectionFoundException as ex:
            LOG.error(ex.message)
            return
        except exceptions.NodeAlreadyHasPortForThisMacAddress as ex:
            LOG.error(ex.message)
            return

        try:
            self.facade.set_node_provision_state(node, 'manage')
        except Exception as ex:
            LOG.error(ex.message)
            return

    def take_manageable_state_actions(self, node):
        LOG.info(
            "Taking manageable state actions for node %(node)s." %
            {'node': node.uuid}
        )

        try:
            self.facade.set_node_provision_state(node, 'provide')
        except Exception as ex:
            LOG.error(ex.message)

    def server_hardware_has_server_profile_applied(self, node):
        server_hardware_uri = self.server_hardware_uri_from_node(
            node
        )
        profile_applied = self.facade.is_server_profile_applied_on_server_hardware(
            server_hardware_uri
        )
        return profile_applied

    def apply_server_profile(self, node):
        assigned_server_profile_uri = self.server_profile_uri_from_node(
            node
        )
        server_profile_template_uri = self.server_profile_template_uri_from_node(
            node
        )
        server_hardware_uri = self.server_hardware_uri_from_node(
            node
        )
        server_profile_name = "Ironic [%s]" % (node.uuid)

        if assigned_server_profile_uri is None:
            assigned_server_profile_uri = self.facade.\
                generate_and_assign_server_profile_from_server_profile_template(
                    server_profile_template_uri,
                    server_profile_name,
                    server_hardware_uri
                )
        else:
            raise exceptions.ServerHardwareAlreadyHasServerProfileException(
                server_hardware_uri,
                assigned_server_profile_uri
            )

    def apply_node_port_configuration(self, node):
        assigned_server_profile_uri = self.server_profile_uri_from_node(
            node
        )
        server_profile_dict = self.facade.get_server_profile(
            assigned_server_profile_uri
        )

        primary_boot_connection = None
        for connection in server_profile_dict.get('connections'):
            boot = connection.get('boot')
            if boot is not None and boot.get('priority').lower() == 'primary':
                primary_boot_connection = connection

        if primary_boot_connection is None:
            raise exceptions.NoBootableConnectionFoundException(
                assigned_server_profile_uri
            )

        server_profile_mac = primary_boot_connection.get('mac')

        port_list_by_mac = self.facade.get_port_list_by_mac(server_profile_mac)
        if not port_list_by_mac:
            self.facade.create_node_port(node.uuid, server_profile_mac)
        else:
            port_obj = self.facade.get_port(port_list_by_mac[0]['uuid'])
            if port_obj['node_uuid'] != node.uuid:
                self.facade.create_node_port(node.uuid, server_profile_mac)
            else:
                raise exceptions.NodeAlreadyHasPortForThisMacAddress(
                    server_profile_mac
                )

    def server_hardware_uri_from_node(self, node):
        return node.driver_info.get(
            'server_hardware_uri'
        )

    def server_profile_template_uri_from_node(self, node):
        node_capabilities = self.capabilities_to_dict(
            node.properties.get('capabilities')
        )
        node_server_profile_template_uri = node_capabilities.get(
            'server_profile_template_uri'
        )
        return node_server_profile_template_uri

    def server_profile_uri_from_node(self, node):
        node_server_hardware_uri = self.server_hardware_uri_from_node(
            node
        )
        uri = self.facade.get_server_profile_assigned_to_sh(
            node_server_hardware_uri
        )
        return uri

    def capabilities_to_dict(self, capabilities):
        """Parse the capabilities string into a dictionary
        :param capabilities: the node capabilities as a formatted string
        :raises: InvalidParameterValue if capabilities is not an string or has
                 a malformed value
        """
        capabilities_dict = {}
        if capabilities:
            if not isinstance(capabilities, six.string_types):
                raise exceptions.InvalidParameterValue(
                    _("Value of 'capabilities' must be string. Got %s")
                    % type(capabilities))
            try:
                for capability in capabilities.split(','):
                    key, value = capability.split(':')
                    capabilities_dict[key] = value
            except ValueError:
                raise exceptions.InvalidParameterValue(
                    _("Malformed capabilities value: %s") % capability
                )
        return capabilities_dict
