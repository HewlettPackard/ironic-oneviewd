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

from ironic_oneviewd.openstack_client import get_ironic_client
from ironic_oneviewd.common import get_oneview_client
from oneview_client import exceptions as oneview_exceptions


class Facade(object):

    def __init__(self, config):
        self.ironicclient = get_ironic_client(config)
        self.oneview_client = get_oneview_client(
            config.oneview.manager_url,
            config.oneview.username,
            config.oneview.password,
            config.oneview.allow_insecure_connections,
            config.oneview.tls_cacert_file,
        )

    # =========================================================================
    # Ironic actions
    # =========================================================================

    def get_ironic_node_list(self):
        return self.ironicclient.node.list(detail=True)

    def get_ironic_node(self, node_uuid):
        return self.ironicclient.node.get(node_uuid)

    def delete_ironic_node(self, node_uuid):
        return self.ironicclient.node.delete(node_uuid)

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

    def get_port_list_by_node_uuid(self, node_uuid):
        return self.ironicclient.port.get(node_id=node_uuid)

    def get_port(self, port_id):
        return self.ironicclient.port.get(port_id)

    def get_port_list_by_mac(self, port_mac_address):
        return self.ironicclient.port.list(address=port_mac_address)

    def create_node_port(self, node_uuid, port_mac_address):
        return self.ironicclient.port.create(node_uuid=node_uuid,
                                             address=port_mac_address)

    # =========================================================================
    # OneView actions
    # =========================================================================

    def get_server_hardware(self, node_info):
        return self.oneview_client.get_server_hardware(node_info)

    def get_server_hardware_state(self, node_info):
        return self.oneview_client.get_server_hardware_state(
            node_info
        )

    def get_server_profile_assigned_to_sh(self, node_info):
        return self.oneview_client.get_server_profile_from_hardware(
            node_info
        )

    def generate_and_assign_server_profile_from_server_profile_template(
        self, server_profile_name, node_info):
        return self.oneview_client.apply_server_profile(
            server_profile_name, node_info
        )

    def unassign_server_profile(self, node_info):
        return self.oneview_client.delete_server_profile_from_server_hardware(
            node_info
        )

    def get_server_hardware_mac(self, uuid):
        sh = self.oneview_client.get_server_hardware_by_uuid(uuid)
        try:
            # MAC from ServerHardware
            mac = sh.get_mac(nic_index=0)
        except oneview_exceptions.OneViewException:
            # MAC from iLO
            mac = self.oneview_client.get_sh_mac_from_ilo(sh.uuid)
        return mac