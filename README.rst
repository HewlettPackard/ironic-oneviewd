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

Installation
============

To install the ironic-oneviewd service, use the following command::

    pip install ironic-oneviewd

Configuring the service
=======================

The ironic-oneviewd uses a configuration file to get Ironic and OneView
credentials and addresses. To configure such file acordingly, run::

    ironic-oneviewd genconfig

This tool asks you for such information and creates a *~/ironic-oneview.conf*
configuration file located at your home directory by default, or other
location of your choice.

Usage
=====

To run ironic-oneviewd, do::

    ironic-oneviewd --config-file <path to your configuration file>

or::

    ironic-oneviewd -c <path to your configuration file>

Note that in order to run this daemon you only have pass the configuration
file previously created containing the required credentials and addresses.

References
==========
.. [1] HP OneView - http://www8.hp.com/us/en/business-solutions/converged-systems/oneview.html

