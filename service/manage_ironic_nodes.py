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

import json
import six

import common
import config_client
#import rabbitmq_client
import service_manager

from ironic.common import exception
from ironic.common.i18n import _

from oslo_log import log as logging

from oneview_client import OneViewServerProfileTemplateAPI
from oneview_client import OneViewServerHardwareAPI
from oneview_client import OneViewServerProfileAPI

LOG = logging.getLogger(__name__)

ENROLL_PROVISION_STATE = 'enroll'
MANAGEABLE_PROVISION_STATE = 'manageable'

supported_drivers = {"agent_pxe_oneview", "iscsi_pxe_oneview", "fake_oneview"}

conf_client = config_client.ConfClient()


def pull_ironic_nodes():
    ironic_nodes = service_manager.get_ironic_node_list()
    for node in ironic_nodes:
        if node.driver in supported_drivers:
            manage_node_provision_state(node)


def manage_node_provision_state(node):
    provision_state = node.provision_state
    if provision_state == ENROLL_PROVISION_STATE:
        take_enroll_state_actions(node)
    elif provision_state == MANAGEABLE_PROVISION_STATE:
        take_manageable_state_actions(node)

def capabilities_to_dict(capabilities):
    """Parse the capabilities string into a dictionary
    :param capabilities: the capabilities of the node as a formatted string.
    :raises: InvalidParameterValue if capabilities is not an string or has a
             malformed value
    """
    capabilities_dict = {}
    if capabilities:
        if not isinstance(capabilities, six.string_types):
            raise exception.InvalidParameterValue(
                _("Value of 'capabilities' must be string. Got %s")
                % type(capabilities))
        try:
            for capability in capabilities.split(','):
                key, value = capability.split(':')
                capabilities_dict[key] = value
        except ValueError:
            raise exception.InvalidParameterValue(
                _("Malformed capabilities value: %s") % capability
            )

    return capabilities_dict

def take_enroll_state_actions(node):
    #TODO (sinval): temos de validar se node_capabilities, node...._uri existem
    #TODO (sinval): validar se essas coisas sao None
    node_server_hardware_uri = node.driver_info.get('server_hardware_uri')
    node_capabilities = capabilities_to_dict(node.properties.get('capabilities'))
    node_server_profile_template_uri = node_capabilities.get('server_profile_template_uri')
    server_hardware_dict = service_manager.get_server_hardware(node_server_hardware_uri)
    sh_server_profile_uri = server_hardware_dict.get('serverProfileUri')
    if sh_server_profile_uri is not None:
        LOG.error("The Server Hardware already has a Server Profile applied.")
    else:
        apply_enroll_node_configuration(node_server_hardware_uri,
            node_server_profile_template_uri, node.uuid)
        service_manager.set_node_provision_state(node, 'manage')

def apply_enroll_node_configuration(server_hardware_uri, server_profile_template_uri, node_uuid):
    server_profile_name = "Ironic [%s]" % (node_uuid)
    server_profile_applied_uri = service_manager.\
        generate_and_assign_server_profile_from_server_profile_template(
            server_profile_template_uri, server_profile_name,
            server_hardware_uri)

    server_profile_dict = service_manager.get_server_profile(server_profile_applied_uri)
    server_profile_mac_address = server_profile_dict.get('connections')[0].get('mac')
    service_manager.create_node_port(node_uuid, server_profile_mac_address)
    #TODO(sinval) config volumes (SAN storage)


def take_manageable_state_actions(node):
    service_manager.set_node_provision_state(node, 'provide')


if __name__ == '__main__':
    pull_ironic_nodes()
