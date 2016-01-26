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

from ironic_oneviewd import service_logging as logging


LOG = logging.getLogger(__name__)

IRONIC_API_VERSION = '1.11'


def get_ironic_client(conf):
    kwargs = {
        'os_username': conf.openstack.admin_user,
        'os_password': conf.openstack.admin_password,
        'os_auth_url': conf.openstack.auth_url,
        'os_tenant_name': conf.openstack.admin_tenant_name,
        'os_ironic_api_version': IRONIC_API_VERSION,
    }
    if conf.openstack.insecure.lower() == 'true':
        kwargs['insecure'] = True
    if conf.openstack.ca_file:
        kwargs['ca_file'] = conf.openstack.ca_file

    LOG.debug("Using OpenStack credentials specified in the configuration file"
              " to get Ironic Client")
    ironicclient = ironic_client.get_client(1, **kwargs)

    return ironicclient
