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
import unittest
from ironic_oneviewd.oneview_client import OneViewServerProfileTemplateAPI
from oneview_client import OneViewServerHardwareAPI
from oneview_client import OneViewServerProfileAPI


SERVER_PROFILE_TEMPLATE_URI =\
    "/rest/server-profile-templates/7bcdabdf-f8a6-455f-9a21-ceb11cd47fff"
SERVER_HARDWARE_URI =\
    "/rest/server-hardware/37333036-3831-4753-4831-30355838524E"
SERVER_PROFILE_NAME_TEST = "new_sp_name"

SERVER_PROFILE_TEST = {'wwnType': 'Virtual',
                       'serialNumberType': 'Virtual',
                       'connections': [
                           {'allocatedMbps': 0,
                            'networkUri': '/rest/ethernet-networks/dffb6d55-6b62-499c-955a-b42673072dfe',
                            'requestedMbps': '2500',
                             'portId': 'Flb 1:1-a',
                             'name': 'dcs-connection',
                             'maximumMbps': 0, 'wwpnType': None,
                             'deploymentStatus': None,
                             'boot': {'priority': 'Primary'},
                             'wwnn': None,
                             'mac': None,
                             'macType': None,
                             'wwpn': None,
                             'interconnectUri': None,
                             'requestedVFs': 'Auto',
                             'functionType': 'Ethernet',
                             'id': 1,
                             'allocatedVFs': None
                            }
                       ],
                       'taskUri': None,
                       'modified': None,
                       'macType': 'Virtual',
                       'category': 'server-profiles',
                       'serverHardwareTypeUri': '/rest/server-hardware-types/C2F7F914-B243-4C1F-89F0-41040964F32E',
                       'uuid': None,
                       'bios': {
                           'overriddenSettings': [],
                           'manageBios': False
                       },
                       'firmware': {
                           'firmwareBaselineUri': None,
                           'manageFirmware': False,
                           'forceInstallFirmware': False,
                           'firmwareInstallType': None
                       },
                       'boot': {
                           'manageBoot': True,
                           'order': ['CD', 'Floppy', 'USB', 'HardDisk', 'PXE']
                       },
                       'hideUnusedFlexNics': True,
                       'bootMode': None,
                       'state': 'Creating',
                       'affinity': 'Bay',
                       'localStorage': {
                           'controllers': []
                       },
                       'type': 'ServerProfileV5',
                       'enclosureUri': None,
                       'associatedServer': None,
                       'status': 'OK',
                       'description': '',
                       'serverProfileTemplateUri': '/rest/server-profile-templates/7bcdabdf-f8a6-455f-9a21-ceb11cd47fff',
                       'eTag': None,
                       'templateCompliance': 'Unknown',
                       'serverHardwareUri': '/rest/server-hardware/37333036-3831-4753-4831-30355838524E',
                       'enclosureBay': None,
                       'name': SERVER_PROFILE_NAME_TEST,
                       'created': None,
                       'serialNumber': None,
                       'enclosureGroupUri': '/rest/enclosure-groups/abd817cb-3313-40d4-886d-5023c98fe062',
                       'uri': None,
                       'sanStorage': {
                           'manageSanStorage': False,
                           'volumeAttachments': []
                       },
                       'inProgress': False}


class OneViewServerProfileTemplateAPITestCase(unittest.TestCase):
    def setUp(self):
        self.server_hardware_uri =\
            "/rest/server-hardware/37333036-3831-4753-4831-30355838524E"

        self.ov_spt_api = OneViewServerProfileTemplateAPI()

    def test_generate_server_profile_from_server_profile_template(self):
        new_server_profile_dict =\
            self.ov_spt_api.generate_server_profile_from_server_profile_template(
            SERVER_PROFILE_TEMPLATE_URI, SERVER_PROFILE_NAME_TEST,
            SERVER_HARDWARE_URI)

        self.assertEquals(
            new_server_profile_dict['name'], SERVER_PROFILE_NAME_TEST)
        self.assertEquals(new_server_profile_dict['serverHardwareUri'],
            SERVER_HARDWARE_URI)

#    def test__assign_server_profile(self):
#       name="new_sp_name"
#
#       sh_dict = self.ov_sh_api.get_server_hardware(self.server_hardware_uri)
#       self.assertIsNone(sh_dict['serverProfileUri'])
#       
#       new_sp = self.ov_spt_api._generate_server_profile_from_server_profile_template(
#           self.server_profile_template_uri, name, self.server_hardware_uri)
#       created_server_profile = self.ov_spt_api._assign_server_profile(new_sp)
#
#       self.assertIsNotNone(created_server_profile['uri'])
#       sh_dict = self.ov_sh_api.get_server_hardware(self.server_hardware_uri)
#       self.assertEquals(sh_dict['serverProfileUri'], created_server_profile['uri'])

       
class OneViewServerProfileAPITestCase(unittest.TestCase):
    def setUp(self):
        self.server_profile = SERVER_PROFILE_TEST
        self.ov_sp_api = OneViewServerProfileAPI()
        self.ov_sh_api = OneViewServerHardwareAPI()

        self._delete_server_profile_from_server_hardware(
            SERVER_PROFILE_TEMPLATE_URI)

    def tearDown(self):
        self._delete_server_profile_from_server_hardware(
            SERVER_PROFILE_TEMPLATE_URI)

    def _delete_server_profile_from_server_hardware(self, server_hardware_uri):
        server_hardware = self.ov_sh_api.get_server_hardware(
            SERVER_HARDWARE_URI)
        # FIXME(afaranha): Deleting Server Profile by name, because I could not
        # find how to delete by the uuid
        if server_hardware['serverProfileUri'] is not None:
            server_profile = self.ov_sp_api.get(server_hardware['serverProfileUri'])
            self.ov_sp_api.delete(server_profile['name'])

    def test_create(self):
        created_server_profile_uri = self.ov_sp_api.create(self.server_profile)
        self.assertIsNotNone(created_server_profile_uri)

    def test_generate_and_assign_server_profile_from_server_profile_template(self):
        server_hardware = self.ov_sh_api.get_server_hardware(
            SERVER_HARDWARE_URI)

        self.assertIsNone(server_hardware['serverProfileUri'])
        server_profile_uri = self.ov_sp_api.\
            generate_and_assign_server_profile_from_server_profile_template(
                SERVER_PROFILE_TEMPLATE_URI, SERVER_PROFILE_NAME_TEST,
                SERVER_HARDWARE_URI)

        server_hardware = self.ov_sh_api.get_server_hardware(
            SERVER_HARDWARE_URI)
        self.assertEquals(
            server_hardware['serverProfileUri'], server_profile_uri)


if __name__ == '__main__':
    unittest.main()
