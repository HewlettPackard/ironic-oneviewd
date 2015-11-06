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

from configparser import ConfigParser
import getpass
import os

# from ironic_oneview_cli.config import ConfClient
# from ironic_oneview_cli.facade import Facade


def do_genconfig(args):
    """Generates the config file according to user input

    """
    print("========= Ironic ========= ")
    ironic_auth_url = raw_input("Type the auth_url for the Ironic service: ")
    ironic_username = raw_input("Type your Ironic username: ")
    ironic_tenant = raw_input("Type your Ironic user's tenant name: ")
    ironic_password = getpass.getpass("Type your Ironic user's password: ")
    ironic_insecure = raw_input("Would you like the connections with Ironic to"
                                " be insecure? [y/N]: ") or "N"
    ironic_insecure = True if ironic_insecure.lower() == 'y' else False
    default_deploy_kernel = raw_input("Type in the default deploy keynel image"
                                      " ID on Glance: ")
    default_deploy_ramdisk = raw_input("Type in the default deploy ramdisk "
                                       "image ID on Glance: ")

# #     defaults = {
# #         "ironic":{
# #             "auth_uri": ironic_auth_uri,
# #             "admin_user": ironic_username,
# #             "admin_tenant": ironic_tenant,
# #             "admin_password": ironic_password,
# #             "insecure": ironic_insecure,
# #         }
# #     }
#     conf = ConfClient('', defaults)
#     facade = Facade(conf)
#     enabled_drivers = facade.get_drivers()
    # TODO(thiagop): get drivers enabled with ironicclient
    enabled_drivers = ['agent_pxe_oneview', 'iscsi_pxe_oneview']
    ironic_default_driver = raw_input(("Which driver would you like to use? "
                                       "[%s]: ") % ','.join(enabled_drivers))

    option = raw_input("Would you like to configure different credentials for"
                       " nova? [y/N]: ")
    option = True if option.lower() == 'y' else False
    if option:
        print("========= Nova ========= ")
        nova_auth_url = raw_input("Type the auth_url for the Nova service: ")
        nova_username = raw_input("Type your Nova username: ")
        nova_tenant = raw_input("Type your Nova user's tenant name: ")
        nova_password = getpass.getpass("Type your Nova user's password: ")
        nova_insecure = raw_input("Would you like the connections with Nova "
                                  "to be insecure? [y/N]: ") or "N"
        nova_insecure = True if nova_insecure.lower() == 'y' else False
    else:
        nova_auth_url = ironic_auth_url
        nova_username = ironic_username
        nova_tenant = ironic_tenant
        nova_password = ironic_password
        nova_insecure = ironic_insecure

    print("========= OneView ========= ")
    oneview_manager_url = raw_input("Type in the OneView uri: ")
    oneview_username = raw_input("Type your OneView username: ")
    oneview_password = getpass.getpass("Type your OneView user's password: ")
    allow_insecure = raw_input("Would you like the connections with OneView "
                               "to be insecure? [y/N]: ") or "N"
    allow_insecure = True if allow_insecure.lower() == 'y' else False

    config = ConfigParser()
    config.add_section("ironic")
    config.set("ironic", "auth_url", ironic_auth_url)
    config.set("ironic", "admin_username", ironic_username)
    config.set("ironic", "admin_tenant_name", ironic_tenant)
    config.set("ironic", "admin_password", ironic_password)
    config.set("ironic", "insecure", ironic_insecure)
    config.set("ironic", "default_deploy_kernel_id", default_deploy_kernel)
    config.set("ironic", "default_deploy_ramdisk_id", default_deploy_ramdisk)
    config.set("ironic", "default_driver", ironic_default_driver)
    config.add_section("nova")
    config.set("nova", "auth_url", nova_auth_url)
    config.set("nova", "username", nova_username)
    config.set("nova", "tenant_name", nova_tenant)
    config.set("nova", "password", nova_password)
    config.set("nova", "insecure", nova_insecure)
    config.add_section("oneview")
    config.set("oneview", "manager_url", oneview_manager_url)
    config.set("oneview", "username", oneview_username)
    config.set("oneview", "password", oneview_password)
    config.set("oneview", "allow_insecure_connections", allow_insecure)

    filename = raw_input("Type the path to the new configuration file [%s]: "
                         % args.config_file) or args.config_file
    full_filename = os.path.realpath(os.path.expanduser(filename))
    directory = os.path.dirname(full_filename)
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(full_filename, 'w') as configfile:
        config.write(configfile)
        print("======\nFile created successfully on '%s'!\n======" % filename)
