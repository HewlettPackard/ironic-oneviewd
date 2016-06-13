===============
Ironic-OneViewd
===============

Overview
========

The ironic-oneviewd is a ``python daemon`` of the OneView Driver for Ironic.
It handles nodes in *enroll* and *manageable* provision states, preparing them
to become *available*. In order to be moved from *enroll* to *available*, a
``Server Profile`` must be applied to the ``Server Hardware`` represented by a
node according to its ``Server Profile Template``.

This daemon monitors Ironic nodes and applies a ``Server Profile`` to such
``Server Hardware``. The node then goes from an *enroll* to a *manageable*
state, and right after to an *available* state.

For more information on OneView entities, see [1]_.

Tested platforms
================

The OneView appliance used for testing was the OneView 2.0.

The Enclosure used for testing was the ``BladeSystem c7000 Enclosure G2``.

The daemon should work on HP Proliant Gen8 and Gen9 Servers supported by
OneView 2.0 and above, or any hardware whose network can be managed by
OneView's ServerProfile. It has been tested with the following servers:

  - Proliant BL460c Gen8
  - Proliant BL465c Gen8
  - Proliant DL360 Gen9 (starting with python-oneviewclient 2.1.0)

Notice here that to the daemon work correctly with Gen8 and Gen9 DL servers
in general, the hardware also needs to run version 4.2.3 of iLO, with Redfish.

Installation
============

To install the ironic-oneviewd service, use the following command::

    pip install ironic-oneviewd

Configuring the service
=======================

The ironic-oneviewd uses a configuration file to get Ironic and OneView
credentials and addresses. To generate and configure such file accordingly,
run::

    ironic-oneviewd genconfig

This tool asks you for such information and creates a *~/ironic-oneviewd.conf*
configuration file located at your home directory by default, or other
location of your choice.

If you prefer to create your own configuration file, it should look like this::

    [DEFAULT]
    retry_interval=<retry interval in seconds>
    rpc_thread_pool_size=<thread pool size>

    [ironic]
    admin_user=<your admin user name>
    admin_password=<your admin password>
    admin_tenant_name=<your admin tenant name>
    auth_url=<your Ironic authentication url>
    insecure=<true,false>
    default_deploy_kernel_id=<your deploy kernel uuid>
    default_deploy_ramdisk_id=<your deploy ramdisk uuid>
    default_driver=<iscsi_pxe_oneview,agent_pxe_oneview,fake_oneview>

    [oneview]
    manager_url=<your OneView appliance url>
    username=<your OneView username>
    password=<your OneView password>
    allow_insecure_connections=<true,false>
    tls_cacert_file=<path to your CA certfile, if any>

Usage
=====

If your *~/ironic-oneviewd.conf* configuration file is in your home directory,
the service will automatically use this conf. In this case, to run
ironic-oneviewd, do::

    ironic-oneviewd

If you chose to place this file in a different location, you should pass it
when starting the service::

    ironic-oneviewd --config-file <path to your configuration file>

or::

    ironic-oneviewd -c <path to your configuration file>

Note that, in order to run this daemon, you only have to pass the
configuration file previously created containing the required credentials
and addresses.

References
==========
.. [1] HP OneView - http://www8.hp.com/us/en/business-solutions/converged-systems/oneview.html
