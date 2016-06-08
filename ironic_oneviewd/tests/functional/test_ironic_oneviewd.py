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
import unittest

from ironic_oneviewd import facade
from ironic_oneviewd.node_manager import manage
from ironic_oneviewd.node_manager.manage import NodeManager
from oneview_client.models import ServerProfile


class FakeIronicNode(object):
    def __init__(self, id, uuid, chassis_uuid, provision_state, driver,
                 ports, driver_info={}, driver_internal_info={},
                 name='fake-node', maintenance='False', properties={},
                 extra={}):

        self.id = id
        self.uuid = uuid
        self.chassis_uuid = chassis_uuid
        self.provision_state = provision_state
        self.driver = driver
        self.ports = ports
        self.driver_info = driver_info
        self.driver_internal_info = driver_internal_info
        self.maintenance = maintenance
        self.properties = properties
        self.extra = extra
        self.name = name


class FakeIronicPort(object):
    def __init__(self, id, uuid, node_uuid, address, extra={},
                 local_link_connection='', portgroup_id='',
                 pxe_enabled='False'):

        self.id = id
        self.uuid = uuid
        self.node_uuid = node_uuid
        self.address = address
        self.extra = extra
        self.local_link_connection = local_link_connection
        self.portgroup_id = portgroup_id
        self.pxe_enabled = pxe_enabled


class FakeConfHelper(object):
    def __init__(self, max_workers):
        self.rpc_thread_pool_size = max_workers


class FakeConfClient(object):
    def __init__(self, max_workers):
        self.DEFAULT = FakeConfHelper(max_workers)


POOL_OF_FAKE_IRONIC_NODES = [
    FakeIronicNode(
        id=123,
        uuid='66666666-7777-8888-9999-000000000000',
        chassis_uuid='aaaaaaaa-1111-bbbb-2222-cccccccccccc',
        maintenance=False,
        provision_state='enroll',
        ports=[
            {'id': 987,
             'uuid': '11111111-2222-3333-4444-555555555555',
             'node_uuid': '66666666-7777-8888-9999-000000000000',
             'address': 'AA:BB:CC:DD:EE:FF',
             'extra': {}}
        ],
        driver='fake_oneview',
        driver_info={'user': 'foo', 'password': 'bar'},
        properties={'num_cpu': 4},
        name='fake-node-1',
        extra={}
    ),
    FakeIronicNode(
        id=123,
        uuid='66666666-7777-8888-9999-000000000000',
        chassis_uuid='aaaaaaaa-1111-bbbb-2222-cccccccccccc',
        maintenance=False,
        provision_state='enroll',
        ports=[
            {'id': 987,
             'uuid': '11111111-2222-3333-4444-555555555555',
             'node_uuid': '66666666-7777-8888-9999-000000000000',
             'address': 'AA:BB:CC:DD:EE:FF',
             'extra': {}}
        ],
        driver='fake_oneview',
        driver_info={
            'dynamic_allocation': True, 'user': 'foo', 'password': 'bar'
        },
        properties={'num_cpu': 4},
        name='fake-node-2',
        extra={}
    )
]

POOL_OF_FAKE_IRONIC_PORTS = [
    FakeIronicPort(
        id=987,
        uuid='11111111-2222-3333-4444-555555555555',
        node_uuid='66666666-7777-8888-9999-000000000000',
        address='AA:BB:CC:DD:EE:FF',
        extra={}
    )
]

FAKE_CONFIG_CLIENT = FakeConfClient(max_workers=20)


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
        node_manager = NodeManager(FAKE_CONFIG_CLIENT)
        node_manager.pull_ironic_nodes()
        mock_get_ironic_node_list.assert_called_with()

    @mock.patch('ironic_oneviewd.facade.Facade', autospec=True)
    @mock.patch.object(manage.NodeManager, 'take_enroll_state_actions')
    def test_manage_node_provision_state_with_node_in_enroll(
        self, mock_take_enroll_state_actions, mock_facade
    ):
        fake_node = copy.deepcopy(POOL_OF_FAKE_IRONIC_NODES[0])
        fake_node.provision_state = 'enroll'
        node_manager = NodeManager(FAKE_CONFIG_CLIENT)
        node_manager.manage_node_provision_state(fake_node)
        mock_take_enroll_state_actions.assert_called_with(fake_node)

    @mock.patch('ironic_oneviewd.facade.Facade', autospec=True)
    @mock.patch.object(manage.NodeManager, 'take_manageable_state_actions')
    def test_manage_node_provision_state_with_node_in_manageable(
        self, mock_take_manageable_state_actions, mock_facade
    ):
        fake_node = copy.deepcopy(POOL_OF_FAKE_IRONIC_NODES[0])
        fake_node.provision_state = 'manageable'
        node_manager = NodeManager(FAKE_CONFIG_CLIENT)
        node_manager.manage_node_provision_state(fake_node)
        mock_take_manageable_state_actions.assert_called_with(fake_node)

    @mock.patch.object(facade.Facade, 'get_port')
    @mock.patch.object(facade.Facade, 'get_server_hardware_state')
    @mock.patch.object(facade.Facade, 'get_port_list_by_mac')
    @mock.patch.object(facade.Facade, 'get_server_profile_assigned_to_sh')
    @mock.patch.object(facade.Facade, 'set_node_provision_state')
    @mock.patch.object(facade.Facade, 'create_node_port')
    @mock.patch('ironic_oneviewd.facade.Facade', autospec=True)
    @mock.patch.object(facade.Facade,
                       'generate_and_assign_sp_from_spt')
    def test_all_enroll_actions(
        self, mock_apply_server_profile, mock_facade,
        mock_create_node_port, mock_set_node_provision_state,
        mock_get_server_profile_assigned_to_sh, mock_get_port_list_by_mac,
        mock_get_server_hardware_state, mock_get_port
    ):

        mocked_facade = facade.Facade(None)
        node_manager = NodeManager(FAKE_CONFIG_CLIENT)

        fake_node = copy.deepcopy(POOL_OF_FAKE_IRONIC_NODES[0])
        fake_node.provision_state = 'enroll'

        info = {'server_hardware_uri': '/rest/server-hardware/123'}
        fake_node.driver_info = info
        mock.patch.dict(fake_node.driver_info, info, clear=True)

        properties = {'capabilities':
                      "server_profile_template_uri:"
                      "/rest/server-profile-templates/123"}
        fake_node.properties = properties
        mock.patch.dict(fake_node.properties, properties, clear=True)

        server_profile = ServerProfile()
        server_profile.connections = [
            {'mac': '01:23:45:67:89:ab', 'boot': {'priority': "primary"}}
        ]

        assigned_server_profile = server_profile
        mock_get_server_profile_assigned_to_sh.return_value = \
            assigned_server_profile
        mocked_facade.get_server_profile_assigned_to_sh = \
            mock_get_server_profile_assigned_to_sh

        server_hardware_state = 'ProfileApplied'
        mock_get_server_hardware_state.return_value = server_hardware_state
        mocked_facade.get_server_hardware_state = \
            mock_get_server_hardware_state

        port_list_by_mac = []
        mock_get_port_list_by_mac.return_value = port_list_by_mac
        mocked_facade.get_port_list_by_mac = mock_get_port_list_by_mac

        fake_port = copy.deepcopy(POOL_OF_FAKE_IRONIC_PORTS[0])
        mock_get_port.return_value = fake_port
        mocked_facade.get_port = mock_get_port

        uri_server_profile_applied = '/rest/server-profiles/123'
        mock_apply_server_profile.return_value = uri_server_profile_applied
        mocked_facade.generate_and_assign_sp_from_spt = \
            mock_apply_server_profile

        port_created = True
        mock_create_node_port.return_value = port_created
        mocked_facade.create_node_port = mock_create_node_port

        node_provision_state_changed = {'node': fake_node.uuid,
                                        'ex_msg': 'manageable'}
        mock_set_node_provision_state.return_value = \
            node_provision_state_changed
        mocked_facade.set_node_provision_state = mock_set_node_provision_state

        node_manager.manage_node_provision_state(fake_node)

        node_info = node_manager.get_node_info_from_node(fake_node)

        mock_apply_server_profile.assert_called_with(
            'Ironic [%(uuid)s]' % {'uuid': fake_node.uuid},
            node_info
        )

        mock_create_node_port.assert_called_with(
            fake_node.uuid,
            '01:23:45:67:89:ab'
        )

        mock_set_node_provision_state.assert_called_with(
            fake_node,
            'manage'
        )

    @mock.patch.object(facade.Facade, 'get_server_hardware_state')
    @mock.patch('ironic_oneviewd.node_manager.manage.LOG.warning')
    @mock.patch.object(facade.Facade, 'get_server_profile_assigned_to_sh')
    @mock.patch.object(facade.Facade, 'get_server_hardware')
    @mock.patch.object(facade.Facade, 'create_node_port')
    @mock.patch('ironic_oneviewd.facade.Facade', autospec=True)
    @mock.patch.object(facade.Facade,
                       'generate_and_assign_sp_from_spt')
    def test_log_warning_when_hardware_already_has_server_profile_applied(
        self, mock_apply_server_profile, mock_facade,
        mock_create_node_port, mock_get_server_hardware,
        mock_get_server_profile_assigned_to_sh, mock_log,
        mock_get_server_hardware_state
    ):
        mocked_facade = facade.Facade(None)
        node_manager = NodeManager(FAKE_CONFIG_CLIENT)

        fake_node = copy.deepcopy(POOL_OF_FAKE_IRONIC_NODES[0])
        fake_node.provision_state = 'enroll'

        info = {'server_hardware_uri': '/rest/server-hardware/123'}
        fake_node.driver_info = info
        mock.patch.dict(fake_node.driver_info, info, clear=True)

        properties = {'capabilities':
                      "server_profile_template_uri:"
                      "/rest/server-profile-templates/123"}
        fake_node.properties = properties
        mock.patch.dict(fake_node.properties, properties, clear=True)

        server_profile = ServerProfile()
        server_profile.name = 'Ironic [%s]' % fake_node.uuid
        server_profile.uri = '/rest/server-profiles/123'
        server_profile.connections = [
            {'mac': fake_node.ports[0]['address'], 'boot': {
                'priority': "primary"}}
        ]

        mock_get_server_profile_assigned_to_sh.return_value = server_profile
        mocked_facade.get_server_profile_assigned_to_sh = \
            mock_get_server_profile_assigned_to_sh
        server_hardware_state = 'ProfileApplied'
        mock_get_server_hardware_state.return_value = server_hardware_state
        mocked_facade.get_server_hardware_state = \
            mock_get_server_hardware_state

        node_manager.manage_node_provision_state(fake_node)

        msg = (
            'Node %s has a Server Profile /rest/server-profiles/123 assigned'
            % (fake_node.uuid)
        )

        mock_log.assert_called_with(msg)

    @mock.patch('ironic_oneviewd.node_manager.manage.LOG.warning')
    @mock.patch.object(facade.Facade, 'get_server_hardware_state')
    @mock.patch.object(facade.Facade, 'get_server_profile_assigned_to_sh')
    @mock.patch.object(facade.Facade, 'get_server_hardware')
    @mock.patch.object(facade.Facade, 'create_node_port')
    @mock.patch('ironic_oneviewd.facade.Facade', autospec=True)
    @mock.patch.object(facade.Facade,
                       'generate_and_assign_sp_from_spt')
    def test_log_warning_when_port_configuration_throw_exception(
        self, mock_apply_server_profile, mock_facade,
        mock_create_node_port, mock_get_server_hardware,
        mock_get_server_profile_assigned, mock_get_server_hardware_state,
        mock_log
    ):
        mocked_facade = facade.Facade(None)
        node_manager = NodeManager(FAKE_CONFIG_CLIENT)

        fake_node = copy.deepcopy(POOL_OF_FAKE_IRONIC_NODES[0])
        fake_node.provision_state = 'enroll'

        info = {'server_hardware_uri': '/rest/server-hardware/123'}
        fake_node.driver_info = info
        mock.patch.dict(fake_node.driver_info, info, clear=True)

        properties = {'capabilities':
                      "server_profile_template_uri:"
                      "/rest/server-profile-templates/123"}
        fake_node.properties = properties
        mock.patch.dict(fake_node.properties, properties, clear=True)

        server_profile = ServerProfile()
        server_profile.name = 'Ironic [%s]' % fake_node.uuid
        server_profile.uri = '/rest/server-profiles/123'
        server_profile.connections = [
            {'mac': '01:23:45:67:89:ab', 'boot': None}
        ]

        assigned_server_profile = server_profile
        mock_get_server_profile_assigned.return_value = assigned_server_profile
        mocked_facade.get_server_profile_assigned_to_sh = \
            mock_get_server_profile_assigned

        server_hardware_state = 'ProfileApplied'
        mock_get_server_hardware_state.return_value = server_hardware_state
        mocked_facade.get_server_hardware_state = \
            mock_get_server_hardware_state

        node_manager.manage_node_provision_state(fake_node)

        msg = (
            "No bootable connection was found for Server Profile "
            "/rest/server-profiles/123"
        )

        mock_log.assert_called_with(msg)

    @mock.patch.object(facade.Facade, 'get_server_hardware_state')
    @mock.patch.object(facade.Facade, 'get_port')
    @mock.patch.object(facade.Facade, 'get_port_list_by_mac')
    @mock.patch('ironic_oneviewd.node_manager.manage.LOG.warning')
    @mock.patch.object(facade.Facade, 'get_server_profile_assigned_to_sh')
    @mock.patch.object(facade.Facade, 'get_server_hardware')
    @mock.patch.object(facade.Facade, 'create_node_port')
    @mock.patch('ironic_oneviewd.facade.Facade', autospec=True)
    @mock.patch.object(facade.Facade,
                       'generate_and_assign_sp_from_spt')
    def test_log_warning_when_node_already_has_port_for_mac_address(
        self, mock_apply_server_profile, mock_facade, mock_create_node_port,
        mock_get_server_hardware, mock_get_server_profile_assigned_to_sh,
        mock_log, mock_get_port_list_by_mac, mock_get_port,
        mock_get_server_hardware_state
    ):
        mocked_facade = facade.Facade(None)
        node_manager = NodeManager(FAKE_CONFIG_CLIENT)

        fake_node = copy.deepcopy(POOL_OF_FAKE_IRONIC_NODES[0])
        fake_node.provision_state = 'enroll'

        info = {'server_hardware_uri': '/rest/server-hardware/123'}
        fake_node.driver_info = info
        mock.patch.dict(fake_node.driver_info, info, clear=True)

        properties = {'capabilities':
                      "server_profile_template_uri:"
                      "/rest/server-profile-templates/123"}
        fake_node.properties = properties
        mock.patch.dict(fake_node.properties, properties, clear=True)

        server_profile = ServerProfile()
        server_profile.connections = [
            {'mac': fake_node.ports[0]['address'], 'boot': {
                'priority': "primary"}}
        ]

        assigned_server_profile = server_profile
        mock_get_server_profile_assigned_to_sh.return_value = \
            assigned_server_profile
        mocked_facade.get_server_profile_assigned_to_sh = \
            mock_get_server_profile_assigned_to_sh
        server_hardware_state = 'ProfileApplied'
        mock_get_server_hardware_state.return_value = server_hardware_state
        mocked_facade.get_server_hardware_state = \
            mock_get_server_hardware_state

        port_list_by_mac = copy.deepcopy(POOL_OF_FAKE_IRONIC_PORTS)
        mock_get_port_list_by_mac.return_value = port_list_by_mac
        mocked_facade.get_port_list_by_mac = mock_get_port_list_by_mac

        fake_port = copy.deepcopy(POOL_OF_FAKE_IRONIC_PORTS[0])
        mock_get_port.return_value = fake_port
        mocked_facade.get_port = mock_get_port

        node_manager.manage_node_provision_state(fake_node)

        msg = (
            "A port with MAC address AA:BB:CC:DD:EE:FF was already "
            "created for this node"
        )

        mock_log.assert_called_with(msg)

    @mock.patch.object(facade.Facade, 'get_port')
    @mock.patch.object(facade.Facade, 'get_server_hardware_state')
    @mock.patch.object(facade.Facade, 'get_port_list_by_mac')
    @mock.patch.object(facade.Facade, 'get_server_profile_assigned_to_sh')
    @mock.patch.object(facade.Facade, 'set_node_provision_state')
    @mock.patch.object(facade.Facade, 'create_node_port')
    @mock.patch.object(facade.Facade, 'get_server_hardware_mac')
    @mock.patch('ironic_oneviewd.facade.Facade', autospec=True)
    @mock.patch.object(facade.Facade,
                       'generate_and_assign_sp_from_spt')
    def test_all_enroll_actions_when_dynamic_allocation_flag_is_true(
        self, mock_apply_server_profile, mock_facade,
        mock_get_server_hardware_mac, mock_create_node_port,
        mock_set_node_provision_state,
        mock_get_server_profile_assigned_to_sh,
        mock_get_port_list_by_mac, mock_get_server_hardware_state,
        mock_get_port
    ):

        mocked_facade = facade.Facade(None)
        node_manager = NodeManager(FAKE_CONFIG_CLIENT)

        fake_node = copy.deepcopy(POOL_OF_FAKE_IRONIC_NODES[1])
        fake_node.provision_state = 'enroll'

        info = {
            'dynamic_allocation': True,
            'server_hardware_uri': '/rest/server-hardware/123'
        }
        fake_node.driver_info = info
        mock.patch.dict(fake_node.driver_info, info, clear=True)

        properties = {'capabilities': ''}
        fake_node.properties = properties
        mock.patch.dict(fake_node.properties, properties, clear=True)

        server_profile = ServerProfile()
        server_profile.connections = [
            {'mac': '01:23:45:67:89:ab', 'boot': {'priority': "primary"}}
        ]

        mock_get_server_hardware_mac.return_value = '01:23:45:67:89:ab'
        mocked_facade.get_server_hardware_mac = mock_get_server_hardware_mac

        assigned_server_profile = server_profile
        mock_get_server_profile_assigned_to_sh.return_value = \
            assigned_server_profile
        mocked_facade.get_server_profile_assigned_to_sh = \
            mock_get_server_profile_assigned_to_sh

        server_hardware_state = 'ProfileApplied'
        mock_get_server_hardware_state.return_value = server_hardware_state
        mocked_facade.get_server_hardware_state = \
            mock_get_server_hardware_state

        port_list_by_mac = []
        mock_get_port_list_by_mac.return_value = port_list_by_mac
        mocked_facade.get_port_list_by_mac = mock_get_port_list_by_mac

        fake_port = copy.deepcopy(POOL_OF_FAKE_IRONIC_PORTS[0])
        mock_get_port.return_value = fake_port
        mocked_facade.get_port = mock_get_port

        uri_server_profile_applied = '/rest/server-profiles/123'
        mock_apply_server_profile.return_value = uri_server_profile_applied
        mocked_facade.generate_and_assign_sp_from_spt = \
            mock_apply_server_profile

        port_created = True
        mock_create_node_port.return_value = port_created
        mocked_facade.create_node_port = mock_create_node_port

        node_provision_state_changed = {'node': fake_node.uuid,
                                        'ex_msg': 'manageable'}
        mock_set_node_provision_state.return_value = \
            node_provision_state_changed
        mocked_facade.set_node_provision_state = mock_set_node_provision_state

        node_manager.manage_node_provision_state(fake_node)

        mock_apply_server_profile.assert_not_called()

        mock_create_node_port.assert_called_with(
            fake_node.uuid,
            '01:23:45:67:89:ab'
        )

        mock_set_node_provision_state.assert_called_with(
            fake_node,
            'manage'
        )


if __name__ == '__main__':
    unittest.main()
