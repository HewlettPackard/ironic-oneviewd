# -*- encoding: utf-8 -*-
#
# Copyright 2016 Hewlett-Packard Development Company, L.P.
# Copyright 2016 Universidade Federal de Campina Grande
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

from ironic_oneviewd import facade
from ironic_oneviewd.oneview_client import get_oneview_client
from ironic_oneviewd.openstack_client import get_ironic_client


class TestIronicOneviewd(unittest.TestCase):

    @mock.patch.object(get_oneview_client, 'get_oneview_client')
    @mock.patch.object(get_ironic_client, 'get_ironic_list')
    @mock.patch.object(facade.Facade, 'get_ironic_node_list')
    def test_take_node_actions(self, mock_get_ironic_node_list):
        facade_mock = facade.Facade()

        mock_get_ironic_node_list().return_value = []
        #self.assertEquals([], mock_get_ironic_node_list.getvalue())
        raise Exception(facade_mock.get_ironic_node_list())

