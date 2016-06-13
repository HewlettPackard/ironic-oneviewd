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

import configparser as ConfigParser

import os

import ironic_oneviewd.service_logging as logging


LOG = logging.getLogger(__name__)


class ConfClient(object):
    def __init__(self, configname, defaults={}):
        self._CONF = ConfigParser.ConfigParser(defaults)
        path = os.path.realpath(os.path.expanduser(configname))
        self._CONF.readfp(open(path))

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

        ret = Section(self._CONF.items(section))
        return ret
