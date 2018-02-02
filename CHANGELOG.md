# 1.2.0

#### Notes
- Deprecate automatic Ironic Port creation, as a new command was added to ironic-oneview-cli
- Remove python-ilorest-library dependency

#### Bugfixes & Enhancements
- Update README
- Enabled tests and coverage evaluation by Travis CI

#### New features
- New CA certificate configuration parameter makes possible to open secure connections to HPE OneView.


# 1.1.0

#### New features
- Filter nodes using the new OneView Hardware Type (since Pike) for driver composition


# 1.0.0

#### Notes
- Deprecate pre-allocation mode
- remove python-oneviewclient dependency
- Add python-hpOneView as dependency

#### Bugfixes & Enhancements
- Fix MAC address retrieval from Server Hardware


# 0.6.0

#### Notes
- Update minimal version of Ironic API to 1.22

#### New features
- Populate local_link_connection field at Ironic Port when using HP OneView Mechanism Driver for Neutron ML2 plugin


# 0.5.1

#### Bugfixes & Enhancements
- Fix server profile application for pre-allocation


# 0.5.0

#### Bugfixes & Enhancements
- Documentation and logs improvements

#### New features
- Introduces hardware inspection when inspection is enabled in the tool conf file
- Introduces endpoint_type for work with public or internal URL's cases


# 0.4.0

#### New features
- Introduces the --log-file parameter to change the logfile path


# 0.3.0

#### Bugfixes & Enhancements
- Using Keystone v3


# 0.2.0

#### New features
- Enrolling nodes with fake_oneview driver for testing purposes


# 0.1.0

#### Bugfixes & Enhancements
- Dealing with dynamic allocation flag
- Using python-oneviewclient for accessing OneView


# 0.0.3

#### Notes
- Add python-oneviewclient>=2.1.0 as requirement

#### New features
- Support for DL server enrollment
- Add python-oneviewclient>=2.1.0 as requirement


# 0.0.2

#### Bugfixes & Enhancements
- Multithreading processing of nodes


# 0.0.1

#### Notes

- Pre-beta version
