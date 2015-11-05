# Ironic-OneViewd

## Overview

The ironic-oneviewd is a Python daemon of the OneView Driver for Ironic. It handle nodes in Enroll
and Manageable state to become Available.

## Installation

To install the ironic-oneviewd tool you can use the following command:

```
pip install ironic-oneviewd
```


## Configuration

The ironic-oneviewd automatically uses *~/ironic-oneview.conf* as default configuration file.
It should contain the credentials that enable the connection with between the daemon, Ironic and OneView.

## Usage

```
ironic-oneviewd --config-file <path to your configuration file> manage-ironic-nodes
```

```
ironic-oneviewd -c <path to your configuration file> manage-ironic-nodes
```

