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

from mock import MagicMock
from mock import patch
from unittest import TestCase

from ironic_oneviewd.facade import Facade
from ironic_oneviewd.oneview_client import get_oneview_client
from ironic_oneviewd.openstack_client import get_ironic_client
from ironic_oneviewd.node_manager.manage import NodeManager

class TestIronicOneviewd(TestCase):

    @patch('ironic_oneviewd.facade.Facade')
    def test_take_node_actions(self, mock):
        self.assertNotIsInstance(mock, Facade)

    @patch.object(Facade, 'get_ironic_node_list', autospec=True)
    def test_number_two(self, mock):
        mock.return_value = []
        self.assertEqual([], mock.return_value)

    @patch.object(NodeManager, 'pull_ironic_nodes', autospec=True)
    @patch.object(Facade, 'get_ironic_node_list', autospec=True)
    def test_pull_ironic_nodes(self, mock_facade_method,
        mock_node_manager_method):
        mock_facade_method.return_value = []

        mock.ironic_nodes.return_value = []
        self.assertEqual([], mock.ironic_nodes)
