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

import mock
import unittest

from oslo_utils import importutils

from ironic_oneviewd.conf import CONF
from ironic_oneviewd import exceptions
from ironic_oneviewd import utils

hponeview_client = importutils.try_import('hpOneView.oneview_client')


class TestUtils(unittest.TestCase):
    def setUp(self):
        self.ov_manager_url = 'https://1.2.3.4'
        self.ov_username = 'user'
        self.ov_password = 'password'
        self.ov_insecure = False
        self.ov_cafile = 'ca_file'

        CONF.oneview.manager_url = self.ov_manager_url
        CONF.oneview.username = self.ov_username
        CONF.oneview.password = self.ov_password
        CONF.oneview.allow_insecure_connections = self.ov_insecure
        CONF.oneview.tls_cacert_file = self.ov_cafile

    @mock.patch.object(hponeview_client, 'OneViewClient', autospec=True)
    def test_get_hponeview_client(self, mock_hponeview_client):
        utils.get_hponeview_client()
        config = {
            "ip": 'https://1.2.3.4',
            "credentials": {
                "userName": 'user',
                "password": 'password'
            },
            "ssl_certificate": 'ca_file'
        }
        mock_hponeview_client.assert_called_once_with(config)

    def test_get_hponeview_client_cafile_none(self):
        CONF.oneview.tls_cacert_file = None
        self.assertRaises(
            exceptions.OneViewNotAuthorizedException,
            utils.get_hponeview_client
        )

    @mock.patch.object(hponeview_client, 'OneViewClient', autospec=True)
    def test_get_hponeview_client_insecure_cafile(self, mock_oneview):
        CONF.oneview.allow_insecure_connections = True
        config = {
            "ip": 'https://1.2.3.4',
            "credentials": {
                "userName": 'user',
                "password": 'password'
            },
            "ssl_certificate": None
        }
        utils.get_hponeview_client()
        mock_oneview.assert_called_once_with(config)
