Ironic-OneViewd
===============

Overview
--------

The ironic-oneviewd is a Python daemon of the OneView Driver for Ironic.
It handle nodes in Enroll and Manageable state to become Available.
To be moved from Enroll to Available, the node must receive the proper Server Profile,
according to its Server Profile Template. The ironic-oneviewd will be monitoring Ironic
nodes, will apply the Server Profile to a Server Hardware represented by a node that
is in Enroll without a Server Profile applied, and will move the node from Enroll to
Manageable and from Manageable to Available.

Installation
------------

To install the ironic-oneviewd tool you can use the following command:

::

    pip install ironic-oneviewd

Configuration
-------------

The ironic-oneviewd automatically uses *~/ironic-oneview.conf* as
default configuration file. It should contain the credentials that
enable the connection with between the daemon, Ironic and OneView.

Usage
-----

::

    ironic-oneviewd --config-file <path to your configuration file>

::

    ironic-oneviewd -c <path to your configuration file>
