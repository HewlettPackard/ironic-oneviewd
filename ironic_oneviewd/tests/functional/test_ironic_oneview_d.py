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

import copy
import mock
import ironicclient
import unittest

from ironic_oneviewd import facade
from ironic_oneviewd import sync_exceptions as exceptions
from ironic_oneviewd.node_manager.manage import NodeManager
import ironic_oneviewd.oneview_client
import ironic_oneviewd.openstack_client
from ironic_oneviewd.node_manager import manage

class FakeIronicNode(object):
    def __init__(self, id, uuid, chassis_uuid, provision_state, driver,
                 driver_info={}, driver_internal_info={}, name='fake-node',
                 maintenance='False', properties={}, extra={}
    ):
        self.id = id
        self.uuid = uuid
        self.chassis_uuid = chassis_uuid
        self.provision_state = provision_state
        self.driver = driver
        self.driver_info = driver_info
        self.driver_internal_info = driver_internal_info
        self.maintenance = maintenance
        self.properties = properties
        self.extra = extra
        self.name = name


POOL_OF_FAKE_IRONIC_NODES = [
    FakeIronicNode(
       id = 123,
       uuid = '66666666-7777-8888-9999-000000000000',
       chassis_uuid = 'aaaaaaaa-1111-bbbb-2222-cccccccccccc',
       maintenance = False,
       provision_state = 'enroll',
       driver = 'fake_oneview',
       driver_info = {'user': 'foo', 'password': 'bar'},
       properties = {'num_cpu': 4},
       name = 'fake-node-1',
       extra = {}
   )
]

class TestIronicOneviewd(unittest.TestCase):

    def setUp(self):
        self.fake_ironic_nodes = POOL_OF_FAKE_IRONIC_NODES

    @mock.patch('ironic_oneviewd.facade.Facade', autospec=True)
    @mock.patch.object(facade.Facade, 'get_ironic_node_list')
    def test_take_node_actions(self, mock_get_ironic_node_list, mock_facade):
       mocked_facade = facade.Facade(None)
       mock_get_ironic_node_list.return_value = self.fake_ironic_nodes
       mocked_facade.get_ironic_node_list = mock_get_ironic_node_list
       mock_facade.return_value = mocked_facade
       node_manager = NodeManager(None)
       node_manager.pull_ironic_nodes()

    @mock.patch('ironic_oneviewd.facade.Facade', autospec=True)
    @mock.patch.object(manage.NodeManager, 'take_enroll_state_actions')
    def test_manage_node_provision_state_with_node_in_enroll(
        self, mock_take_enroll_state_actions, mock_facade
    ):
        fake_node = copy.deepcopy(POOL_OF_FAKE_IRONIC_NODES[0])
        fake_node.provision_state = 'enroll'
        node_manager = NodeManager(None)
        node_manager.manage_node_provision_state(fake_node)
        mock_take_enroll_state_actions.assert_called_with(fake_node)


    @mock.patch('ironic_oneviewd.facade.Facade', autospec=True)
    @mock.patch.object(manage.NodeManager, 'take_manageable_state_actions')
    def test_manage_node_provision_state_with_node_in_manageable(
        self, mock_take_manageable_state_actions, mock_facade
    ):
        fake_node = copy.deepcopy(POOL_OF_FAKE_IRONIC_NODES[0])
        fake_node.provision_state = 'manageable'
        node_manager = NodeManager(None)
        node_manager.manage_node_provision_state(fake_node)
        mock_take_manageable_state_actions.assert_called_with(fake_node)

    @mock.patch('ironic_oneviewd.facade.Facade', autospec=True)
    def test_manage_node_provision_state_with_node_in_maintenance(
        self, mock_facade
    ):
        fake_node = copy.deepcopy(POOL_OF_FAKE_IRONIC_NODES[0])
        fake_node.maintenance = True
        node_manager = NodeManager(None)
        self.assertRaises(exceptions.NodeInMaintenance,
                          node_manager.manage_node_provision_state,
                          fake_node
        )


    @mock.patch.object(facade.Facade,
        'get_server_hardware')
    @mock.patch.object(facade.Facade,
        'create_node_port')
    @mock.patch.object(facade.Facade, 
        'get_server_profile')
    @mock.patch('ironic_oneviewd.facade.Facade', autospec=True)
    @mock.patch.object(facade.Facade, 
        'generate_and_assign_server_profile_from_server_profile_template')
    def test_applying_server_profile(
        self, mock_apply_server_profile, mock_facade, mock_get_server_profile,
        mock_create_node_port, mock_get_server_hardware
    ):
	mocked_facade = facade.Facade(None)
	mock_apply_server_profile.return_value = '/rest/server-profile/123'
	mock_get_server_profile.return_value = \
        {'connections': {'mac': '01:23:45:67:89:ab'}}
	mock_get_server_hardware.return_value = {}

        fake_node = copy.deepcopy(POOL_OF_FAKE_IRONIC_NODES[0])
        fake_node.provision_state = 'enroll'
        fake_node.driver_info = {'server_hardware_uri': '/rest/server-hardware/123'}
        fake_node.properties = {'capabilities': 
                "{'server_profile_template_uri':'/rest/server-profile-template/123'}"}
        node_manager = NodeManager(None)
        node_manager.manage_node_provision_state(fake_node)


        mock_create_node_port.assert_called_with(fake_node.uuid, '01:23:45:67:89:ab')
