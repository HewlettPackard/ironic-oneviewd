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
import ironic_oneviewd.oneview_client
import ironic_oneviewd.openstack_client
from ironic_oneviewd.node_manager import manage

class TestIronicOneviewd(unittest.TestCase):

    def test_take_node_actions(self):
        #mock_function = mock.create_autospec(
        #    ironic_oneviewd.openstack_client.get_ironic_client,
        #    return_value='a'
        #)
        facade.Facade = mock.create_autospec(facade.Facade)
        mock_get_ironic_node_list = mock.create_autospec(
            facade.Facade.get_ironic_node_list(), return_value=[]
        )
        
        self.facade = facade.Facade(None)
        self.facade.get_ironic_node_list = mock_get_ironic_node_list
        self.assertEquals([], mock_get_ironic_node_list())
        manager = manage.NodeManager(None)
        manager.facade = self.facade
        result = manager.pull_ironic_nodes()
        raise Exception(result)
        #raise Exception(self.facade.get_ironic_node_list())
