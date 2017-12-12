[![PyPI version](https://badge.fury.io/py/ironic-oneviewd.svg)](https://badge.fury.io/py/ironic-oneviewd)
[![Build Status](https://travis-ci.org/HewlettPackard/ironic-oneviewd.svg?branch=master)](https://travis-ci.org/HewlettPackard/ironic-oneviewd)
[![Coverage Status](https://coveralls.io/repos/github/HewlettPackard/ironic-oneviewd/badge.svg)](https://coveralls.io/github/HewlettPackard/ironic-oneviewd)

# Ironic OneView Daemon

## Overview

The ironic-oneviewd is a ``python daemon`` of the OneView Driver for OpenStack Ironic. It helps the cloud administrator by handling nodes in *enroll* and *manageable* provision states, preparing them to become *available*. To be moved from *enroll* to *available*, a ``Server Profile`` must be applied to the ``Server Hardware`` represented by a node according to its ``Server Profile Template``.

This daemon monitors Ironic nodes and applies a ``Server Profile`` to such ``Server Hardware``.

Then, the node goes from an *enroll* to a *manageable* state, and right after to an *available* state.

> This tool works with OpenStack Identity API v2.0 and v3.

For more information on OneView entities, see [here](https://www.hpe.com/us/en/integrated-systems/software.html).

## Tested platforms

The OneView appliance used for testing was the OneView 3.0.

The Enclosure used for testing was:

  - HPE BladeSystem c7000 Enclosure G2.
  - HPE Synergy

The daemon should work on HPE Proliant Gen8 and Gen9 Servers supported by OneView 2.0 and above, or any hardware whose network can be managed by OneView Server Profile. It has been tested with the following servers:

  - HPE Proliant BL460c Gen8
  - HPE Proliant BL465c Gen8
  - HPE Proliant DL360 Gen9

Notice here that to the daemon worked correctly with Gen8 and Gen9 DL servers in general, the hardware also needs to run version 4.2.3 of iLO, with Redfish.

## Installation

To install the ironic-oneviewd service, use the following command:

    pip install ironic-oneviewd

## Configuration

The ironic-oneviewd uses a configuration file to get Ironic and OneView credentials and addresses. By default, ironic-oneviewd tries to use the configuration file:

    /etc/ironic-oneviewd/ironic-oneviewd.conf

A sample configuration file is found within the same directory and may be used as base for the configuration file. In order to do so, the sample file needs to be renamed to ``ironic-oneviewd.conf``. The sample configuration file is found as follows:

    /etc/ironic-oneviewd/ironic-oneviewd.conf.sample

## Usage

If your configuration file is in the default directory */etc/ironic-oneviewd/ironic-oneviewd.conf*, the service will automatically use this file. In this case, to run ironic-oneviewd, do:

    ironic-oneviewd

If you chose to place this file in a different location, you should pass it when starting the service:

    ironic-oneviewd --config-file <path to your configuration file>

or:

    ironic-oneviewd -c <path to your configuration file>

Note that, to run this daemon, you only have to pass the configuration file previously created that contains the required credentials and addresses.

When ironic-oneviewd is executed, the default output is the standard output. Otherwise, if the --log-file parameter is passed at the execution, the logs will be appended to the log file path and not shown on the standard output. You should pass it when starting the service:

    ironic-oneviewd --log-file <path to your logging file>

## Contributing

Fork it, branch it, change it, commit it, and pull-request it. We are passionate about improving this project, and are glad to accept help to make it better. However, keep the following in mind: We reserve the right to reject changes that we feel do not fit the scope of this project. For feature additions, please open an issue to discuss your ideas before doing the work.

## Feature Requests

If you have a need not being met by the current implementation, please let us know (via a new issue). This feedback is crucial for us to deliver a useful product. Do not assume that we have already thought of everything, because we assure you that is not the case.

## Testing

We have already packaged everything you need to do to verify if the code is passing the tests. The tox script wraps the unit tests execution against Python 2.7, 3.5 and pep8 validations.

Run the following command::

    tox
