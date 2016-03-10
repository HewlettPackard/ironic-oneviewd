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


class FakeConfClient(object):
    def __init__(self, defaults={}):
        self._DEFAULTS = defaults

    def __getattr__(self, section):

        class Section(object):
            def __init__(self, cfg_section):
                self.__dict__ = dict(cfg_section)

            def __getattribute__(self, *args, **kwargs):
                try:
                    return object.__getattribute__(self, *args, **kwargs)
                except AttributeError:
                    raise AttributeError("Missing required attribute '%s' on "
                                         "section '%s' " % (args[0], section))

        ret = Section(self._DEFAULTS.get(section, {}))
        return ret
