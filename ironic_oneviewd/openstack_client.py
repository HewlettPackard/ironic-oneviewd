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

from ironicclient import client as ironic_client
from novaclient import client as nova_client

from ironic_oneviewd.config import ConfClient
from ironic_oneviewd.oneview_client import OneViewServerHardwareAPI
from ironic_oneviewd import service_logging as logging


LOG = logging.getLogger(__name__)

IRONIC_API_VERSION = '1.11'


def get_ironic_client(conf):
    kwargs = {
        'os_username': conf.ironic.admin_user,
        'os_password': conf.ironic.admin_password,
        'os_auth_url': conf.ironic.auth_url,
        'os_tenant_name': conf.ironic.admin_tenant_name,
        'os_ironic_api_version': IRONIC_API_VERSION,
    }
    if conf.ironic.insecure.lower() == 'true':
        kwargs['insecure'] = True
    if conf.ironic.ca_file:
        kwargs['ca_file'] = conf.ironic.ca_file

    LOG.debug("Using OpenStack credentials specified in the configuration file"
              " to get Ironic Client")
    ironicclient = ironic_client.get_client(1, **kwargs)
    return ironicclient


def get_nova_client(conf):
    kwargs = {
        'auth_url': conf.nova.auth_url,
        'username': conf.nova.username,
        'password': conf.nova.password,
        'tenant_name': conf.nova.tenant_name
    }
    if conf.nova.insecure.lower() == 'true':
        kwargs['insecure'] = True
    if conf.nova.ca_file:
        kwargs['ca_file'] = conf.nova.ca_file
    else:
        kwargs['ca_file'] = None
    LOG.debug("Using OpenStack credentials specified in the configuration file"
              " to get Nova Client")
    nova = nova_client.Client(2, conf.nova.username,
                              conf.nova.password,
                              conf.nova.tenant_name,
                              conf.nova.auth_url,
                              kwargs['insecure'],
                              kwargs['ca_file'])
    return nova


class OpenstackClient:
    def __init__(self, configname, **kwargs):
        self.conf_client = ConfClient(configname)
        self.ca_file = kwargs.get('os_cacert')
        self.insecure = kwargs.get('os_insecure', False)

    def _update_ironic_node_state(self, node, server_hardware_uri):
        oneview_sh_client = OneViewServerHardwareAPI()
        state = oneview_sh_client.get_node_power_state(server_hardware_uri)

        LOG.info('Setting node %(node_uuid)s power state to %(state)s',
                 {'node_uuid': node.uuid, 'state': state})

        self._get_ironic_client().node.set_power_state(node.uuid, state)

    def set_ironic_node_provision_state(self, node, target_state):
        LOG.debug('Setting node %(node_uuid)s provision state to %(state)s',
                  {'node_uuid': node.uuid, 'state': target_state})
        ironic_client = self._get_ironic_client()
        ironic_client.node.set_provision_state(node.uuid, target_state)

    def create_ironic_node_port(self, node_uuid, port_mac):
        LOG.debug(
            'Creating port for node %(node_uuid)s', {'node_uuid': node_uuid}
        )
        ironic_client = self._get_ironic_client()
        ironic_client.port.create(node_uuid=node_uuid, address=port_mac)

    def _is_flavor_available(self, server_hardware_info):
        LOG.info("Getting flavors from nova")
        for flavor in self.get_nova_client().flavors.list():
            extra_specs = flavor.get_keys()
            if('capabilities:server_hardware_type_uri' in extra_specs):
                if(extra_specs.get('capabilities:server_hardware_type_uri') !=
                    server_hardware_info.get('server_hardware_type_uri')):
                    continue
                if(extra_specs.get('cpu_arch') !=
                    server_hardware_info.get('cpu_arch')):
                    continue
                if(flavor._info.get('vcpus') !=
                    server_hardware_info.get('cpus')):
                    continue
                if(flavor._info.get('ram') !=
                    server_hardware_info.get('memory_mb')):
                    continue
                return True
        return False

    def flavor_list(self):
        nova_client = self.get_nova_client()
        return nova_client.flavors.list()
