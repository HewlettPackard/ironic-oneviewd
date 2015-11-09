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

from ironic_oneviewd.oneview_client import get_oneview_client
from ironic_oneviewd.openstack_client import get_ironic_client
from ironic_oneviewd.openstack_client import get_nova_client


class Facade(object):

    def __init__(self, config):
        self.ironicclient = get_ironic_client(config)
        self.novaclient = get_nova_client(config)
        self.oneviewclient = get_oneview_client(config)

    # =========================================================================
    # Ironic actions
    # =========================================================================
    def get_ironic_node_list(self):
        return self.ironicclient.node.list(detail=True)

    def get_ironic_node(self, node_uuid):
        return self.ironicclient.node.get(node_uuid)

    def node_set_maintenance(self, node_uuid, maintenance_mode, maint_reason):
        return self.ironicclient.node.set_maintenance(
            node_uuid,
            maintenance_mode,
            maint_reason=maint_reason
        )

    def create_ironic_node(self, **attrs):
        return self.ironicclient.node.create(**attrs)

    def set_node_provision_state(self, node, state):
        return self.ironicclient.node.set_provision_state(node.uuid, state)

    def create_node_port(self, node_uuid, port_mac_address):
        return self.ironicclient.port.create(node_uuid=node_uuid,
                                             address=port_mac_address)

    # =========================================================================
    # OneView actions
    # =========================================================================

    def prepare_and_do_ov_requests(self, uri, body={}, request_type='GET',
                                   api_version='120'):
        return self.oneviewclient.prepare_and_do_request(uri, body,
                                                         request_type,
                                                         api_version)

    def get_server_hardware(self, uri):
        return self.oneviewclient.server_hardware.get_server_hardware(uri)

    def get_server_profile_assigned_to_sh(self, server_hardware_uri):
        return self.oneviewclient.server_hardware.get_server_profile_assigned_to_sh(server_hardware_uri)

    def parse_server_hardware_to_dict(self, server_hardware_json):
        return self.oneviewclient.server_hardware.parse_server_hardware_to_dict(server_hardware_json)

    def get_ov_server_hardware_list(self,):
        return self.oneviewclient.server_hardware.get_server_hardware_list()

    def get_ov_server_power_state(self, driver_info):
        return self.oneviewclient.server_hardware.get_node_power_state(
            driver_info)

    def get_server_profile(self, server_profile_uri):
        return self.oneviewclient.server_profile.get_server_profile_template(
            server_profile_uri)

    def generate_and_assign_server_profile_from_server_profile_template(
        self, server_profile_template_uri, server_profile_name,
        server_profile_server_hardware_uri):
        return self.oneviewclient.server_profile.generate_and_assign_server_profile_from_server_profile_template(
            server_profile_template_uri, server_profile_name,
            server_profile_server_hardware_uri)

    def clone_and_assign_server_profile(self, server_hardware_uri,
                                        server_profile_template_uri,
                                        node_uuid):
        return self.oneviewclient.server_profile.clone_and_assign(
            server_hardware_uri, server_profile_template_uri, node_uuid)

    def unassign_server_profile(self, server_hardware_uri, server_profile_uri):
        return self.oneviewclient.server_profile.unassign_server_profile(server_hardware_uri, server_profile_uri)
