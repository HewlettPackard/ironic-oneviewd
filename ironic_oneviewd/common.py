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

from ironic_oneviewd.openstack.common._i18n import _
from ironic_oneviewd import sync_exceptions
import oneview_client


REQUIRED_ON_PROPERTIES = {
    'server_hardware_type_uri': _("Server Hardware Type URI Required."),
    'server_profile_template_uri': _("Server Profile Template URI required"),
}

REQUIRED_ON_EXTRAS = {
    'server_hardware_uri': _("Server Hardware URI. Required."),
}


def node_has_server_profile(driver_info):
    server_hardware = oneview_client.get_server_hardware(driver_info)
    server_profile_uri = server_hardware.get("serverProfileUri")
    return server_profile_uri is not None


def verify_node_properties(node):
    properties = node.properties.get('capabilities', '')
    for key in REQUIRED_ON_PROPERTIES:
        if key not in properties:
            raise sync_exceptions.MissingParameterValue(
                _("Missing the following OneView data in node's "
                  "properties/capabilities: %s.") % key
            )

    return properties


def verify_node_extra(node):
    extra = node.extra or {}
    for key in REQUIRED_ON_EXTRAS:
        if not extra.get(key):
            raise sync_exceptions.MissingParameterValue(
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
            raise sync_exceptions.InvalidParameterValue(
                _("Malformed capabilities value: %s") % capability
            )

    return capabilities_dict
