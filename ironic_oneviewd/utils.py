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

from oslo_utils import importutils

from ironic_oneviewd import exceptions
from ironic_oneviewd.openstack.common._i18n import _
from ironic_oneviewd import service_logging as logging

client = importutils.try_import('oneview_client.client')
oneview_states = importutils.try_import('oneview_client.states')
oneview_exceptions = importutils.try_import('oneview_client.exceptions')

REQUIRED_ON_PROPERTIES = {
    'server_hardware_type_uri': _("Server Hardware Type URI Required."),
    'server_profile_template_uri': _("Server Profile Template URI required"),
}

REQUIRED_ON_EXTRAS = {
    'server_hardware_uri': _("Server Hardware URI. Required."),
}

IRONIC_API_VERSION = 1

LOG = logging.getLogger(__name__)


def get_ironic_client(conf):

    os_insecure = True if conf.openstack.insecure == 'True' else False
    daemon_kwargs = {
        'os_username': conf.openstack.username,
        'os_password': conf.openstack.password,
        'os_auth_url': conf.openstack.auth_url,
        'os_region_name': conf.openstack.region_name,
        'insecure': os_insecure,
        'os_cacert': conf.openstack.cacert,
        'os_cert': conf.openstack.cert,
        'os_project_id': conf.openstack.project_id,
        'os_project_name': conf.openstack.project_name,
        'os_tenant_id': conf.openstack.tenant_id,
        'os_tenant_name': conf.openstack.tenant_name,
        'os_user_domain_id': conf.openstack.user_domain_id,
        'os_user_domain_name': conf.openstack.user_domain_name,
        'os_project_domain_id': conf.openstack.project_domain_id,
        'os_project_domain_name': conf.openstack.project_domain_name,
        'os_ironic_api_version': '1.11'
    }

    LOG.debug("Using OpenStack credentials specified in the configuration "
              "file to get Ironic Client")

    return ironic_client.get_client(IRONIC_API_VERSION, **daemon_kwargs)


def get_oneview_client(config):
    """Generates an instance of the OneView client.

    Generates an instance of the OneView client using the imported
    oneview_client library.

    :returns: an instance of the OneView client
    """
    audit_enabled = True if config.oneview.audit_enabled == 'True' else False
    ov_insecure = (
        True if config.oneview.allow_insecure_connections == 'True' else False)

    oneview_client = client.Client(
        manager_url=config.oneview.manager_url,
        username=config.oneview.username,
        password=config.oneview.password,
        allow_insecure_connections=ov_insecure,
        tls_cacert_file=config.oneview.tls_cacert_file,
        max_polling_attempts=int(config.oneview.max_polling_attempts),
        audit_enabled=audit_enabled,
        audit_map_file=config.oneview.audit_map_file,
        audit_output_file=config.oneview.audit_output_file
    )
    return oneview_client


def verify_node_properties(node):
    properties = node.properties.get('capabilities', '')
    for key in REQUIRED_ON_PROPERTIES:
        if key not in properties:
            raise exceptions.MissingParameterValue(
                _("Missing the following OneView data in node's "
                  "properties/capabilities: %s.") % key
            )

    return properties


def verify_node_extra(node):
    extra = node.extra or {}
    for key in REQUIRED_ON_EXTRAS:
        if not extra.get(key):
            raise exceptions.MissingParameterValue(
                _("Missing the following OneView data in node's extra: %s.")
                % key
            )

    return extra


def capabilities_to_dict(capabilities):
    capabilities_dict = {}
    if capabilities:
        try:
            for capability in capabilities.split(','):
                key, value = capability.split(':')
                capabilities_dict[key] = value
        except ValueError:
            raise exceptions.InvalidParameterValue(
                _("Malformed capabilities value: %s") % capability
            )

    return capabilities_dict


def dynamic_allocation_enabled(node):
    flag = node.driver_info.get('dynamic_allocation')
    if flag:
        if str(flag).lower() == 'true':
            return True
        elif str(flag).lower() == 'false':
            return False
        else:
            msg = (("Invalid dynamic_allocation parameter value "
                    "'%(flag)s' in node's %(node_uuid)s driver_info. "
                    "Valid values are booleans true or false.") %
                   {"flag": flag, "node_uuid": node.uuid})
            raise exceptions.InvalidParameterValue(msg)
    return False
