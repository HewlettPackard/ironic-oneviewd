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

from concurrent import futures
import six

from ironic_oneviewd import facade
from ironic_oneviewd import service_logging as logging
from ironic_oneviewd import sync_exceptions
from ironic_oneviewd.openstack.common._i18n import _


LOG = logging.getLogger(__name__)

ENROLL_PROVISION_STATE = 'enroll'
MANAGEABLE_PROVISION_STATE = 'manageable'

MAX_WORKERS = 20

class NodeManager:
    def __init__(self, conf_client):

        self.supported_drivers = {"agent_pxe_oneview",
                                  "iscsi_pxe_oneview",
                                  "fake_oneview"}

        self.conf_client = conf_client
        self.facade = facade.Facade(conf_client)

    def pull_ironic_nodes(self):
        ironic_nodes = self.facade.get_ironic_node_list()
        LOG.info("%(len_nodes)s Ironic nodes has been taken."
                  % {"len_nodes": len(ironic_nodes)}
        )
        nodes = [node for node in ironic_nodes
                 if node.driver in self.supported_drivers]

        workers = min(MAX_WORKERS, len(nodes))
        with futures.ThreadPoolExecutor(max_workers=workers) as executor:
            result = executor.map(self.manage_node_provision_state, nodes)

    def manage_node_provision_state(self, node):
        provision_state = node.provision_state
        if node.maintenance:
            return
        elif provision_state == ENROLL_PROVISION_STATE:
            self.take_enroll_state_actions(node)
        elif provision_state == MANAGEABLE_PROVISION_STATE:
            self.take_manageable_state_actions(node)


    def capabilities_to_dict(self, capabilities):
        """Parse the capabilities string into a dictionary
        :param capabilities: the node capabilities as a formatted string
        :raises: InvalidParameterValue if capabilities is not an string or has
                 a malformed value
        """
        capabilities_dict = {}
        if capabilities:
            if not isinstance(capabilities, six.string_types):
                raise sync_exceptions.InvalidParameterValue(
                    _("Value of 'capabilities' must be string. Got %s")
                    % type(capabilities))
            try:
                for capability in capabilities.split(','):
                    key, value = capability.split(':')
                    capabilities_dict[key] = value
            except ValueError:
                raise sync_exceptions.InvalidParameterValue(
                    _("Malformed capabilities value: %s") % capability
                )

        return capabilities_dict

    def take_enroll_state_actions(self, node):
        LOG.debug("Taking enroll state actions for node %(node)s."
                  % {"node": node.uuid})
        node_server_hardware_uri = node.driver_info.get('server_hardware_uri')
        node_capabilities = self.capabilities_to_dict(
            node.properties.get('capabilities'))
        node_server_profile_template_uri = node_capabilities.get(
            'server_profile_template_uri')

        assigned_server_profile_uri = self.facade.\
            get_server_profile_assigned_to_sh(node_server_hardware_uri)
        if assigned_server_profile_uri is None:
            server_profile_name = "Ironic [%s]" % (node.uuid)
            assigned_server_profile_uri = self.facade.\
                generate_and_assign_server_profile_from_server_profile_template(
                    node_server_profile_template_uri, server_profile_name,
                    node_server_hardware_uri)
        else:
            LOG.warning("Server Hardware %(sh_uri)s already has a Server "
                        "Profile %(sp_uri)s assigned. Skipping this task." %
                        {"sh_uri": node_server_hardware_uri,
                         "sp_uri": assigned_server_profile_uri})

        try:
            self.apply_enroll_node_port_configuration(node.uuid, assigned_server_profile_uri)
            self.facade.set_node_provision_state(node, 'manage')
        except Exception as ex:
            exc_msg = ("Error handling the node %(node)s to manageable state."
                       " %(ex_msg)s" % {"node": node.uuid,
                                        "ex_msg": ex.message})
            LOG.error(exc_msg)
            raise Exception(exc_msg)

    def apply_enroll_node_port_configuration(self, node_uuid, server_profile_uri):
        server_profile_dict = self.facade.get_server_profile(server_profile_uri)

        primary_boot_connection = None
        for connection in server_profile_dict.get('connections'):
            boot = connection.get('boot')
            if boot is not None and boot.get('priority').lower() == 'primary':
                primary_boot_connection = connection

        if primary_boot_connection is None:
            message = ("No primary boot connection configured for Server "
                       "Profile %s. Unable to create a port in Ironic."
                       % server_profile_uri)
            raise Exception(message)

        server_profile_mac = primary_boot_connection.get('mac')

        node_port = self.facade.get_node_port_by_mac_address(server_profile_mac)
        if node_port is None:
            self.facade.create_node_port(node_uuid, server_profile_mac)
        else:
            LOG.warning("A port with %(mac)s MAC address was already created."
                        "Skipping this task." % {"mac": server_profile_mac})

    def take_manageable_state_actions(self, node):
        LOG.debug("Taking manageable state actions for node %(node)s."
                  % {"node": node.uuid}
        )
        try:
            self.facade.set_node_provision_state(node, 'provide')
        except Exception as ex:
            raise Exception("Error handling the node %(node)s to"
                            " available state. %(ex_msg)s" %
                            {"node": node.uuid, "ex_msg": ex.message}
                  )
