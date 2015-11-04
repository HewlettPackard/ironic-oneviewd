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

from oslo_config import cfg

from oneview_client import OneViewClient
from openstack_client import OpenstackClient

opts = [
    cfg.StrOpt('default_deploy_kernel_id',
               help='Deploy kernel image used by the synch mechanism'),
    cfg.StrOpt('default_deploy_ramdisk_id',
               help='Deploy ramdisk image used by the synch mechanism'),
    cfg.StrOpt('default_sync_driver',
               help='Default driver to synch with OneView'),
]

CONF = cfg.CONF
CONF.register_opts(opts, group='ironic')
CONF(default_config_files=['sync.conf'])

os_client = OpenstackClient()
ov_client = OneViewClient()
sh_api = ov_client.server_hardware_api
sp_api = ov_client.server_profile_api

def get_config_options():
    return CONF


#===============================================================================
# Ironic actions
#===============================================================================

def get_ironic_client():
    return os_client._get_ironic_client()


def update_ironic_node_state(node, server_hardware_uri):
    return os_client._update_ironic_node_state(node, server_hardware_uri)


def get_ironic_node_list():
    return get_ironic_client().node.list(detail=True)


def get_ironic_node(node_uuid):
    return get_ironic_client().node.get(node_uuid)


def node_set_maintenance(node_uuid, maintenance_mode, maint_reason):
    return get_ironic_client().node.set_maintenance(node_uuid, maintenance_mode, maint_reason=maint_reason)


def set_node_provision_state(node, state):
    return os_client.set_ironic_node_provision_state(node, state)


def create_node_port(node_uuid, port_mac_address):
    return os_client.create_ironic_node_port(node_uuid, port_mac_address)


#===============================================================================
# Nova actions
#===============================================================================

def get_nova_client():
    return os_client._get_nova_client()


def is_nova_flavor_available(server_hardware_info):
    return os_client._is_flavor_available(server_hardware_info)


#===============================================================================
# OneView actions
#===============================================================================

def prepare_and_do_ov_requests(uri, body={}, request_type='GET', api_version='120'):
    return sp_api.prepare_and_do_request(uri, body, request_type, api_version)


def get_server_hardware(uri):
    return sh_api.get_server_hardware(uri)


def get_server_profile_assigned_to_sh(server_hardware_uri):
    return sh_api.get_server_profile_assigned_to_sh(server_hardware_uri)


def parse_server_hardware_to_dict(server_hardware_json):
    return ov_client.server_hardware_api.parse_server_hardware_to_dict(server_hardware_json)


def get_ov_server_hardware_list():
    return ov_client.server_hardware_api.get_server_hardware_list()


def get_ov_server_power_state(driver_info):
    return ov_client.server_hardware_api.get_node_power_state(driver_info)


def create_ironic_node(server_hardware_info):
    return o


def get_server_profile(server_profile_uri):
    return sp_api.get_server_profile_template(server_profile_uri) # get_server_profile

def generate_and_assign_server_profile_from_server_profile_template(
    server_profile_template_uri, server_profile_name,
    server_profile_server_hardware_uri):
    return sp_api.generate_and_assign_server_profile_from_server_profile_template(
        server_profile_template_uri, server_profile_name,
        server_profile_server_hardware_uri)

def clone_and_assign_server_profile(server_hardware_uri,
                                    server_profile_template_uri, node_uuid):
    return sp_api.clone_and_assign(server_hardware_uri,
                                      server_profile_template_uri, node_uuid)

def unassign_server_profile(server_hardware_uri, server_profile_uri):
    return sp_api.unassign_server_profile(server_hardware_uri, server_profile_uri)
