# Copyright (2016-2017) Hewlett Packard Enterprise Development LP
# Copyright (2016-2017) Universidade Federal de Campina Grande
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

from ironic_oneviewd.conf import CONF
from ironic_oneviewd import facade
from ironic_oneviewd.inventory_manager import manage as inventory_manager
from ironic_oneviewd.node_manager import manage as node_manager
from ironic_oneviewd import utils


class FakeIronicNode(object):
    def __init__(self, id, uuid, provision_state, driver, last_error='',
                 driver_info={}, maintenance='False', properties={}):

        self.id = id
        self.uuid = uuid
        self.provision_state = provision_state
        self.driver = driver
        self.last_error = last_error
        self.driver_info = driver_info
        self.maintenance = maintenance
        self.properties = properties


POOL_OF_FAKE_IRONIC_NODES = [
    FakeIronicNode(
        id=1,
        uuid='66666666-7777-8888-9999-333',
        maintenance=False,
        provision_state='enroll',
        driver='fake_oneview',
        driver_info={
            'user': 'foo', 'password': 'bar',
            'server_hardware_uri': '/rest/server-hardware-types/111122223333'
        },
        properties={'num_cpu': 4}
    ),
    FakeIronicNode(
        id=2,
        uuid='66666666-7777-8888-9999-2222',
        maintenance=False,
        provision_state='manageable',
        driver='fake_oneview',
        driver_info={
            'user': 'foo', 'password': 'bar'
        },
    ),
    FakeIronicNode(
        id=3,
        uuid='66666666-7777-8888-9999-1111',
        maintenance=False,
        provision_state='inspect failed',
        driver='fake_oneview',
        last_error='is already in use by OneView.',
        driver_info={
            'user': 'foo',
            'password': 'bar',
            'server_hardware_uri': '/rest/server-hardware-types/111122223344'
        }
    ),
    FakeIronicNode(
        id=4,
        uuid='66666666-7777-222-555-1111',
        maintenance=False,
        provision_state='inspect failed',
        driver='fake_oneview',
        driver_info={
            'user': 'foo',
            'password': 'bar',
            'server_hardware_uri': '/rest/server-hardware-types/111122223344'
        }
    ),
    FakeIronicNode(
        id=5,
        uuid='66666666-7777-2222-9999-1111',
        maintenance=False,
        provision_state='enroll',
        driver='fake_driver',
        driver_info={
            'user': 'foo',
            'password': 'bar',
        }
    ),
    FakeIronicNode(
        id=6,
        uuid='66666666-8888-8888-9999-1111',
        maintenance=True,
        provision_state='enroll',
        driver='fake_oneview',
        driver_info={
            'user': 'foo',
            'password': 'bar',
            'server_hardware_uri': '/rest/server-hardware-types/100122223344'
        }
    )
]

FakeProfileTemplate = {
    'uuid': '1111-2222-3333-4444',
    'serverHardwareTypeUri': 'rest/server-hardware/11223344',
    'enclosureGroupUri': 'rest/enclosure-group/3322211'
}


class TestIronicOneviewd(unittest.TestCase):
    @mock.patch.object(utils, 'get_ironic_client')
    @mock.patch.object(utils, 'get_hponeview_client')
    @mock.patch("time.sleep", side_effect=ValueError)
    def test_node_manager(self, mock_sleep, mock_oneview, mock_ironic):
        ironic_client = mock_ironic()
        ironic_client.node.list.return_value = POOL_OF_FAKE_IRONIC_NODES
        test_facade = facade.Facade()
        node_manage = node_manager.NodeManager(test_facade)

        with self.assertRaises(ValueError):
            node_manage.run()

        # NOTE(nicodemos): Set Provision State called for nodes 1, 2, 3
        self.assertEqual(
            3, ironic_client.node.set_provision_state.call_count)

    @mock.patch.object(utils, 'get_ironic_client')
    @mock.patch.object(utils, 'get_hponeview_client')
    @mock.patch("time.sleep", side_effect=ValueError)
    def test_inventory_manager(self, mock_sleep, mock_oneview, mock_ironic):
        CONF.inventory.server_profile_templates = ['1111-2222-3333-4444']
        oneview_client = mock_oneview()
        oneview_client.server_profile_templates.get.return_value = (
            FakeProfileTemplate
        )
        ironic_client = mock_ironic()
        ironic_client.node.list.return_value = POOL_OF_FAKE_IRONIC_NODES
        test_facade = facade.Facade()
        inventory_manage = inventory_manager.InventoryManager(test_facade)

        with self.assertRaises(ValueError):
            inventory_manage.run()

        oneview_client.server_hardware.get_all.assert_called_with(
            filter=["serverHardwareTypeUri='rest/server-hardware/11223344'",
                    "serverGroupUri='rest/enclosure-group/3322211'"])
