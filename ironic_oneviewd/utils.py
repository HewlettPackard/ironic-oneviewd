# Copyright (2015-2017) Hewlett Packard Enterprise Development LP
# Copyright (2015-2017) Universidade Federal de Campina Grande
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

from ironicclient import client as ironic_client
from oslo_log import log as logging
from oslo_utils import importutils

from ironic_oneviewd.conf import CONF
from ironic_oneviewd import exceptions

LOG = logging.getLogger(__name__)

hpclient = importutils.try_import('hpOneView.oneview_client')
oneview_exceptions = importutils.try_import('hpOneView.exceptions')

REQUIRED_ON_PROPERTIES = {
    'server_hardware_type_uri': "Server Hardware Type URI Required.",
    'server_profile_template_uri': "Server Profile Template URI required",
}

REQUIRED_ON_EXTRAS = {
    'server_hardware_uri': "Server Hardware URI. Required.",
}

IRONIC_API_VERSION = 1

SUPPORTED_CLASSIC_DRIVERS = [
    'agent_pxe_oneview',
    'iscsi_pxe_oneview',
    'fake_oneview'
]
SUPPORTED_HARDWARE_TYPES = ['oneview']
SUPPORTED_DRIVERS = SUPPORTED_HARDWARE_TYPES + SUPPORTED_CLASSIC_DRIVERS


def get_ironic_client():
    """Generate an instance of the Ironic client.

    This method creates an instance of the Ironic client using the OpenStack
    credentials from config file and the ironicclient library.

    :returns: an instance of the Ironic client
    """
    daemon_kwargs = {
        'os_username': CONF.openstack.username,
        'os_password': CONF.openstack.password,
        'os_auth_url': CONF.openstack.auth_url,
        'os_region_name': CONF.openstack.region_name,
        'insecure': CONF.openstack.insecure,
        'os_cacert': CONF.openstack.cacert,
        'os_cert': CONF.openstack.cert,
        'os_endpoint_type': CONF.openstack.endpoint_type,
        'os_project_id': CONF.openstack.project_id,
        'os_project_name': CONF.openstack.project_name,
        'os_tenant_id': CONF.openstack.tenant_id,
        'os_tenant_name': CONF.openstack.tenant_name,
        'os_user_domain_id': CONF.openstack.user_domain_id,
        'os_user_domain_name': CONF.openstack.user_domain_name,
        'os_project_domain_id': CONF.openstack.project_domain_id,
        'os_project_domain_name': CONF.openstack.project_domain_name,
        'os_ironic_api_version': '1.32'
    }

    try:
        client = ironic_client.get_client(IRONIC_API_VERSION, **daemon_kwargs)
    except Exception as exc:
        LOG.error(exc.msg)
        raise exc

    return client


def get_hponeview_client():
    """Generate an instance of the hpOneView client.

    Generates an instance of the hpOneView client using the hpOneView
    oneview_client library.

    :returns: an instance of the OneView client
    :raises: OneViewNotAuthorizedException if is not an insecure connection and
             there is no CA certificate file path in configuration.
    """
    insecure = CONF.oneview.allow_insecure_connections
    ssl_certificate = CONF.oneview.tls_cacert_file

    if not (insecure or ssl_certificate):
        LOG.error("Failed to start Ironic OneView Daemon. Attempting to open "
                  "secure connection to OneView but CA certificate file is "
                  "missing. Please check your configuration file. Will "
                  "attempt to start again...")
        raise exceptions.OneViewNotAuthorizedException()
    elif insecure:
        LOG.info("Ironic OneView Daemon is opening an insecure connection to "
                 "HPE OneView. We recommend you to configure secure "
                 "connections with a CA certificate file.")

        if ssl_certificate:
            LOG.info("Insecure connection to OneView, the CA certificate "
                     "file: %s will be ignored." % ssl_certificate)
            ssl_certificate = None

    config = {
        "ip": CONF.oneview.manager_url,
        "credentials": {
            "userName": CONF.oneview.username,
            "password": CONF.oneview.password
        },
        "ssl_certificate": ssl_certificate
    }

    try:
        client = hpclient.OneViewClient(config)
    except oneview_exceptions.HPOneViewException as exc:
        LOG.error(
            "Ironic OneView Daemon could not open a connection to HPE "
            "OneView. Check credentials and/or CA certificate file. See "
            "details on error below:\n")
        raise exc

    return client


def arg(*args, **kwargs):
    """Decorator for CLI args.

    Example:

    >>> @arg("name", help="Name of the new entity")
    ... def entity_create(args):
    ...     pass
    """
    def _decorator(func):
        add_arg(func, *args, **kwargs)
        return func
    return _decorator


def add_arg(func, *args, **kwargs):
    """Bind CLI arguments to a shell.py `do_foo` function."""
    if not hasattr(func, 'arguments'):
        func.arguments = []

    # NOTE(sirp): avoid dups that can occur when the module is shared across
    # tests.
    if (args, kwargs) not in func.arguments:
        # Because of the semantics of decorator composition if we just append
        # to the options list positional options will appear to be backwards.
        func.arguments.insert(0, (args, kwargs))


def verify_node_properties(node):
    properties = node.properties.get('capabilities', '')
    for key in REQUIRED_ON_PROPERTIES:
        if key not in properties:
            raise exceptions.MissingParameterValue(
                ("Missing the following OneView data in node's "
                 "properties/capabilities: %s.") % key)

    return properties


def verify_node_extra(node):
    extra = node.extra or {}
    for key in REQUIRED_ON_EXTRAS:
        if not extra.get(key):
            raise exceptions.MissingParameterValue(
                "Missing the following OneView data in node's extra: %s." % key
            )

    return extra


def capabilities_to_dict(capabilities):
    """Parse the capabilities string into a dictionary.

    :param capabilities: the node capabilities as a formatted string
    :raises: InvalidParameterValue if capabilities is not an string or has
             a malformed value
    """
    capabilities_dict = {}
    if capabilities:
        if not isinstance(capabilities, six.string_types):
            raise exceptions.InvalidParameterValue(
                "Value of 'capabilities' must be string. Got %s" %
                type(capabilities))
        try:
            for capability in capabilities.split(','):
                key, value = capability.split(':')
                capabilities_dict[key] = value
        except ValueError:
            raise exceptions.InvalidParameterValue(
                "Malformed capabilities value: %s" % capability)
    return capabilities_dict


def get_node_info_from_node(node):
    capabilities_dict = capabilities_to_dict(
        node.properties.get('capabilities', '')
    )
    driver_info = node.driver_info
    oneview_info = {
        'server_hardware_uri':
            driver_info.get('server_hardware_uri'),
        'server_hardware_type_uri':
            capabilities_dict.get('server_hardware_type_uri'),
        'enclosure_group_uri':
            capabilities_dict.get('enclosure_group_uri'),
        'server_profile_template_uri':
            capabilities_dict.get('server_profile_template_uri') or
            driver_info.get('server_profile_template_uri')
    }
    return oneview_info


def node_has_hardware_propeties(node):
    properties = [node.properties.get("memory_mb"),
                  node.properties.get("cpu_arch"),
                  node.properties.get("local_gb"),
                  node.properties.get("cpus")]
    return all(properties)


def server_profile_template_uri_from_node(node):
    node_capabilities = capabilities_to_dict(
        node.properties.get('capabilities')
    )
    node_server_profile_template_uri = node_capabilities.get(
        'server_profile_template_uri'
    )
    return node_server_profile_template_uri


def get_ilo_access(remote_console):
    url = remote_console.get('remoteConsoleUrl')
    url_parse = six.moves.urllib.parse.urlparse(url)
    [host_ip] = six.moves.urllib.parse.parse_qs(url_parse.netloc).get('addr')
    [token] = six.moves.urllib.parse.parse_qs(
        url_parse.netloc).get('sessionkey')

    return host_ip, token


def server_hardware_uri_from_node(node):
    return node.driver_info.get('server_hardware_uri')


def server_hardware_uuid_from_node(node):
    uri = server_hardware_uri_from_node(node)
    return uuid_from_uri(uri)


def uuid_from_uri(uri):
    return uri.split("/")[-1]
