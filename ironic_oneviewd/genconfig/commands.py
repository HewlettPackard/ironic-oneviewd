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
    """Generates the config file according to user input"""

    print("========= DEFAULT ========")
    retry_interval = input(
        "Type the polling interval in seconds for daemon to manage the nodes. "
        "e.g., 300 for every 5 minutes: ") or "300"
    rpc_thread_pool_size = input(
        "Type the size of the RPC thread pool: ") or "20"

    print("========= OpenStack ========= ")
    os_auth_url = input("Type the auth_url for the Ironic service: ")
    os_username = input("Type your OpenStack username: ")
    os_password = getpass.getpass("Type your OpenStack password: ")
    os_region_name = input("Type the Keystone region name: ")
    os_insecure = input("Would you like to allow insecure connections "
                        "to OpenStack? [y/N]: ")
    os_insecure = 'True' if os_insecure.lower() == 'y' else 'False'
    os_cacert = input("Type the path of OpenStack cacert file: ")
    os_cert = input("Type the path of OpenStack cert file: ")

    os_identity_version = input("Type the OpenStack Identity API version "
                                "(Supported versions: 2/3 - Default=3): ")
    os_identity_version = '2' if os_identity_version == '2' else '3'

    if os_identity_version == '3':
        os_project_id = input("Type your OpenStack project id: ")
        os_project_name = input("Type your OpenStack project name: ")
        os_user_domain_id = input("Type your OpenStack user domain ID: ")
        os_user_domain_name = input("Type your OpenStack user domain name: ")
        os_project_domain_id = input("Type your OpenStack project domain ID: ")
        os_project_domain_name = input(
            "Type your OpenStack project domain name: ")
    else:
        os_tenant_id = input("Type your OpenStack tenant id: ")
        os_tenant_name = input("Type your OpenStack tenant name: ")

    deploy_kernel = input(
        "Type in the default deploy keynel image ID on Glance: ")
    deploy_ramdisk = input(
        "Type in the default deploy ramdisk image ID on Glance: ")

    # TODO(thiagop): get drivers enabled with ironicclient
    oneview_drivers = [
        'agent_pxe_oneview', 'iscsi_pxe_oneview', 'fake_oneview'
    ]
    ironic_driver = input(
        ("Which driver would you like to use? [%s]: ") % ','.join(
            oneview_drivers
        )
    )

    print("========= OneView ========= ")
    oneview_manager_url = input("Type in the OneView uri: ")
    oneview_username = input("Type your OneView username: ")
    oneview_password = getpass.getpass("Type your OneView user's password: ")
    oneview_insecure = input("Would you like to allow insecure connections "
                             "to OneView? [y/N]: ")
    oneview_insecure = 'True' if oneview_insecure.lower() == 'y' else 'False'
    oneview_audit = input("Would you like to enable OneView audit? [y/N]: ")
    oneview_audit = 'True' if oneview_audit.lower() == 'y' else 'False'

    if oneview_audit == 'True':
        oneview_audit_input = input("OneView Audit input file path: ")
        oneview_audit_output = input("OneView Audit output file path: ")

    config = ConfigParser()
    config.set("DEFAULT", "retry_interval", retry_interval)
    config.set("DEFAULT", "rpc_thread_pool_size", rpc_thread_pool_size)

    config.add_section("openstack")
    config.set("openstack", "auth_url", os_auth_url)
    config.set("openstack", "username", os_username)
    config.set("openstack", "password", os_password)
    config.set("openstack", "region_name", os_region_name)
    config.set("openstack", "insecure", os_insecure)
    config.set("openstack", "cacert", os_cacert)
    config.set("openstack", "cert", os_cert)

    if os_identity_version == '3':
        config.set("openstack", "project_id", os_project_id)
        config.set("openstack", "project_name", os_project_name)
        config.set("openstack", "user_domain_id", os_user_domain_id)
        config.set("openstack", "user_domain_name", os_user_domain_name)
        config.set("openstack", "project_domain_id", os_project_domain_id)
        config.set("openstack", "project_domain_name", os_project_domain_name)
    else:
        config.set("openstack", "tenant_id", os_tenant_id)
        config.set("openstack", "tenant_name", os_tenant_name)

    config.set("openstack", "deploy_kernel_id", deploy_kernel)
    config.set("openstack", "deploy_ramdisk_id", deploy_ramdisk)
    config.set("openstack", "ironic_driver", ironic_driver)

    config.add_section("oneview")
    config.set("oneview", "manager_url", oneview_manager_url)
    config.set("oneview", "username", oneview_username)
    config.set("oneview", "password", oneview_password)
    config.set("oneview", "allow_insecure_connections", oneview_insecure)
    config.set("oneview", "audit_enabled", oneview_audit)

    if oneview_audit == 'True':
        config.set("oneview", "audit_map_file", oneview_audit_input)
        config.set("oneview", "audit_output_file", oneview_audit_output)

    filename = input("Type the path of the new configuration file [%s]: "
                     % args.config_file) or args.config_file
    full_filename = os.path.realpath(os.path.expanduser(filename))
    directory = os.path.dirname(full_filename)

    if not os.path.exists(directory):
        os.makedirs(directory)

    with open(full_filename, 'w') as configfile:
        config.write(configfile)
        print("======\nFile created successfully on '%s'!\n======" % filename)
