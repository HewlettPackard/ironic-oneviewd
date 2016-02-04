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
        raise ("blablabla")
        nodes = [node for node in ironic_nodes
                 if node.driver in self.supported_drivers]
        self.manage_node_provision_state(nodes[0])
        workers = min(MAX_WORKERS, len(nodes))
        with futures.ThreadPoolExecutor(max_workers=workers) as executor:
            result = executor.map(self.manage_node_provision_state, nodes)

    def manage_node_provision_state(self, node):
        provision_state = node.provision_state
        if node.maintenance:
            raise sync_exceptions.NodeInMaintenance(
                "The node %(node)s is in maintenance state."
                " Ignoring it." % {'node': node.uuid}
            )
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
                  % {"node": node.uuid}
        )

        node_server_hardware_uri = node.driver_info.get('server_hardware_uri')
        node_capabilities = self.capabilities_to_dict(
            node.properties.get('capabilities')
        )
        node_server_profile_template_uri = node_capabilities.get(
            'server_profile_template_uri'
        )
        server_hardware_dict = self.facade.get_server_hardware(
            node_server_hardware_uri
        )
        sh_server_profile_uri = server_hardware_dict.get('serverProfileUri')
        if sh_server_profile_uri is not None:
	    raise Exception(server_hardware_dict)
            LOG.error("The Server Hardware already has a "
                      "Server Profile applied.")
        else:
            self.apply_enroll_node_configuration(
                node_server_hardware_uri,
                node_server_profile_template_uri,
                node.uuid
            )

            try:
                self.facade.set_node_provision_state(node, 'manage')
            except Exception as ex:
                raise Exception("Error handling the node %(node)s to"
                                " manageable state. %(ex_msg)s" %
                                {"node": node.uuid, "ex_msg": ex.message}
                      )

    def apply_enroll_node_configuration(self, server_hardware_uri,
                                        server_profile_template_uri,
                                        node_uuid):
	raise Exception("heueuheuhe")
        server_profile_name = "Ironic [%s]" % (node_uuid)
        sp_applied_uri = self.facade.\
            generate_and_assign_server_profile_from_server_profile_template(
                server_profile_template_uri, server_profile_name,
                server_hardware_uri)

        sp_dict = self.facade.get_server_profile(sp_applied_uri)
        server_profile_mac = sp_dict.get('connections')[0].get('mac')
        self.facade.create_node_port(node_uuid, server_profile_mac)

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
