# Copyright 2017 Hewlett Packard Enterprise Development LP
# Copyright 2017 Universidade Federal de Campina Grande
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

import time

from oslo_log import log as logging
from oslo_utils import importutils

from ironic_oneviewd.conf import CONF
from ironic_oneviewd import utils

client_exception = importutils.try_import('hpOneView.exceptions')

LOG = logging.getLogger(__name__)


class InventoryManager(object):
    def __init__(self, facade):
        self.facade = facade

    def run(self):
        check_interval = CONF.inventory.check_interval

        while True:
            ironic_nodes = self.facade.get_ironic_node_list()
            profile_templates = CONF.inventory.server_profile_templates
            oneview_nodes = [node for node in ironic_nodes
                             if node.driver in utils.SUPPORTED_DRIVERS
                             if node.maintenance is False]
            if profile_templates:
                self.check_not_enrolled_hardware(
                    oneview_nodes, profile_templates)
            else:
                LOG.info("There is no Server Profile Templates to check.")

            time.sleep(check_interval)

    def check_not_enrolled_hardware(self, oneview_nodes, profile_templates):
        """Check the Servers Hardware that is not enrolled in Ironic nodes.

        This method will log all Servers Hardware that is not enrolled as an
        Ironic node. This Server Hardware is using a specific Server Profile
        Template passed in Ironic OneView Daemon configuration file.

        :param oneview_nodes: Ironic nodes using OneView supported drivers.
        :param profile_templates: List of Server Profile Templates.
        """
        enrolled_hardware = []
        if oneview_nodes:
            enrolled_hardware = [node.driver_info.get(
                'server_hardware_uri') for node in oneview_nodes]

        for server_profile_template in profile_templates:
            try:
                template_object = self.facade.get_server_profile_template(
                    server_profile_template)
                server_hardware = self._get_server_hardware_list(
                    template_object)
            except client_exception.HPOneViewException as ex:
                LOG.error(ex.msg)
                continue
            LOG.info("Checking not enrolled Server Hardware using the "
                     "Server Profile Template: %(spt)s" %
                     {'spt': template_object.get('uri')})
            for sh in server_hardware:
                if sh.get('uri') not in enrolled_hardware:
                    LOG.info("Server Hardware: %(sh)s is not enrolled "
                             "as an Ironic node." % {'sh': sh.get('uri')})

    def _get_server_hardware_list(self, server_profile_template):
        """Get a list of Servers Hardware using same Server Profile Template.

        This method get all Servers Hardware compatible with the Server
        Profile Template.

        :param server_profile_template:Server Profile Template object.
        :returns: A sorted list by name of Servers Hardware.
        """
        selected_sht_uri = server_profile_template.get(
            'serverHardwareTypeUri'
        )
        selected_eg_uri = server_profile_template.get(
            'enclosureGroupUri'
        )
        hardware_type_uri = "serverHardwareTypeUri='%s'" % selected_sht_uri
        hardware_filter = [hardware_type_uri]

        # NOTE(nicodemos): Rack Servers are not in any enclosure
        if selected_eg_uri:
            enclosure_group_uri = "serverGroupUri='%s'" % selected_eg_uri
            hardware_filter.append(enclosure_group_uri)

        try:
            hardware_list = self.facade.filter_server_hardware_available(
                hardware_filter)
        except client_exception.HPOneViewException as ex:
            LOG.error(ex.msg)

        return sorted(
            hardware_list, key=lambda x: x.get('name').lower())
