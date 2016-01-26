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

import getpass
import os

from builtins import input
from configparser import ConfigParser


def do_genconfig(args):
    """Generates the config file according to user input

    """
    print("========= DEFAULT ========")
    default_retry_interval = input("Type the retry interval for daemon manage the nodes, e.g., 10, for 10 seconds: ")
    retry_interval = default_retry_interval if default_retry_interval else "300"

    print("========= Openstack ========= ")
    openstack_auth_url = input("Type the auth_url for the Ironic service: ")
    openstack_username = input("Type your Openstack username: ")
    openstack_tenant = input("Type your Openstack user's tenant name: ")
    openstack_password = getpass.getpass("Type your Openstack user's password: ")
    openstack_insecure = input("Would you like the connections with Openstack"
                               "to be insecure? [y/N]: ") or "N"
    openstack_insecure = 'True' if openstack_insecure.lower() == 'y' else 'False'
    default_deploy_kernel = input("Type in the default deploy keynel image"
                                  " ID on Glance: ")
    default_deploy_ramdisk = input("Type in the default deploy ramdisk "
                                   "image ID on Glance: ")

    # TODO(thiagop): get drivers enabled with ironicclient
    enabled_drivers = ['agent_pxe_oneview', 'iscsi_pxe_oneview']
    ironic_default_driver = input(("Which driver would you like to use? "
                                   "[%s]: ") % ','.join(enabled_drivers))

    print("========= OneView ========= ")
    oneview_manager_url = input("Type in the OneView uri: ")
    oneview_username = input("Type your OneView username: ")
    oneview_password = getpass.getpass("Type your OneView user's password: ")
    allow_insecure = input("Would you like the connections with OneView "
                           "to be insecure? [y/N]: ") or "N"
    allow_insecure = 'True' if allow_insecure.lower() == 'y' else 'False'

    config = ConfigParser()
    config.set("DEFAULT", "retry_interval", retry_interval)
    config.add_section("openstack")
    config.set("openstack", "auth_url", openstack_auth_url)
    config.set("openstack", "admin_user", openstack_username)
    config.set("openstack", "admin_tenant_name", openstack_tenant)
    config.set("openstack", "admin_password", openstack_password)
    config.set("openstack", "insecure", openstack_insecure)
    config.set("openstack", "default_deploy_kernel_id", default_deploy_kernel)
    config.set("openstack", "default_deploy_ramdisk_id", default_deploy_ramdisk)
    config.set("openstack", "default_driver", ironic_default_driver)
    config.add_section("oneview")
    config.set("oneview", "manager_url", oneview_manager_url)
    config.set("oneview", "username", oneview_username)
    config.set("oneview", "password", oneview_password)
    config.set("oneview", "allow_insecure_connections", allow_insecure)

    filename = input("Type the path to the new configuration file [%s]: "
                     % args.config_file) or args.config_file
    full_filename = os.path.realpath(os.path.expanduser(filename))
    directory = os.path.dirname(full_filename)
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(full_filename, 'w') as configfile:
        config.write(configfile)
        print("======\nFile created successfully on '%s'!\n======" % filename)
