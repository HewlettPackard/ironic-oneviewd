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

import json
import os
import time

import requests

import config_client
import oneview_uri

from ironic.common.i18n import _LE
from ironic.common.i18n import _LI
from ironic.common import states

from ironic.common.i18n import _
from oslo_config import cfg
from oslo_config import types
from oslo_log import log as logging

import sync_exceptions as exception 

import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

LOG = logging.getLogger(__name__)

ONEVIEW_POWER_ON = 'On'
ONEVIEW_POWER_OFF = 'Off'

def get_oneview_client(conf):
    kwargs = {
        'username': conf.oneview.username,
        'password': conf.oneview.password,
        'manager_url': conf.oneview.manager_url,
        'allow_insecure_connections': False,
        'tls_cacert_file': ''
    }
    if conf.oneview.allow_insecure_connections.lower() == 'true':
        kwargs['allow_insecure_connections'] = True
    if conf.oneview.tls_cacert_file:
        kwargs['tls_cacert_file'] = conf.oneview.tls_cacert_file
    return OneViewClient(**kwargs)
    

class OneViewRequestAPI:
    def __init__(self, manager_url, username, password,
                 allow_insecure_connections, tls_cacert_file):
        self.token = None
        self.manager_url = manager_url
        self.username = username
        self.password = password
        self.tls_cacert_file = tls_cacert_file
        self.allow_insecure_connections = allow_insecure_connections
        self.max_retries = 50

    def _wait_task_completes_returning_status(self, task_uri, max_waiting_time=10):
        def _check_task_status(task_uri):
            task = self.prepare_and_do_request(uri=task_uri)
            if task['associatedResource']['resourceUri'] is not None:
                return TASK_STATUS_OK
            elif len(task['taskErrors']) > 0:
                return TASK_STATUS_ERROR
            return TASK_STATUS_WAITING

        slept_time = 0
        while _check_task_status(task_uri) == TASK_STATUS_WAITING and\
            slept_time <= max_waiting_time:
            time.sleep(1)
            slept_time += 1

        return self.prepare_and_do_request(uri=task_uri)

    def _get_verify_connection_option(self):
        verify_status = False
        user_cacert = self.tls_cacert_file
        if self.allow_insecure_connections is False:
            if(user_cacert is None):
                verify_status = True
            else:
                verify_status = user_cacert
        return verify_status


    def _is_token_valid(self):
        return self.token is not None


    def _try_execute_request(self, url, request_type, body, headers,
                             verify_status):
        try:
            return requests.request(request_type, url, data=json.dumps(body),
                                    headers=headers, verify=verify_status)
        except requests.RequestException as ex:
            LOG.error(_LE("Can't connect to OneView: %s")
                      % (str(ex.message).split(':')[-1]))
            LOG.error(("Can't connect to OneView: %s")
                      % (str(ex.message).split(':')[-1]))
            raise exception.OneViewConnectionError(
                "Can't connect to OneView: %s" % str(ex.message))


    def _new_token(self):
        LOG.info(_LI("Using OneView credentials specified in configuration file"))
        url = '%s%s' % (self.manager_url,
                        oneview_uri.AUTHENTICATION_URL)
        body = {
            'password': self.password,
            'userName': self.username
        }
        headers = {'content-type': 'application/json'}
        verify_status = self._get_verify_connection_option()
        if verify_status is False:
            LOG.warn('Using insecure connection')
        json_response = None
        repeat = True
        while repeat:
            r = self._try_execute_request(url, 'POST', body, headers,
                                      verify_status)
            # NOTE: Workaround to fix JsonDecode problems
            try:
                json_response = r.json()
                repeat = self._check_request_status(r)
            except:
                repeat = True
        return json_response.get('sessionID')


    def _update_token(self):
        if not self._is_token_valid():
            self.token = self._new_token()


    def _check_request_status(self, response):
        repeat = False
        status = response.status_code
        response_json = response.json()
        if status in (409,):
            ignored_conflicts = {'RABBITMQ_CLIENTCERT_CONFLICT'}
            if (response_json.get('errorCode') in ignored_conflicts):
                repeat = False
            else:
                time.sleep(10)
                repeat = True
            LOG.debug("Conflict contacting OneView: ", response_json)
        elif status in (404, 500):
            LOG.error(_LE("Error contacting OneView: "), response_json)
            LOG.error(("Error contacting OneView: "), response_json)
        elif status not in (200, 202):
            LOG.warn("Status not recognized:", status, response_json)
        return repeat


    def prepare_and_do_request(self, uri, body={}, request_type='GET', api_version='200'):
        max_retries=self.max_retries
        
        self._update_token()
        headers = {
           'content-type': 'application/json',
           'X-Api-Version': api_version,
           'Auth': self.token
        }
        url = '%s%s' % (self.manager_url, uri)
        verify_status = self._get_verify_connection_option()
        
        json_response = None
        repeat = True
        retries = 0
        while repeat and (retries < max_retries):
            r = self._try_execute_request(url, request_type, body, headers,
                                          verify_status)
            # NOTE: Workaround to fix JsonDecode problems
            try:
                json_response = r.json()
                repeat = self._check_request_status(r)
            except Exception as ex:
                repeat = True
                retries += 1
        return json_response


class OneViewCertificateAPI(OneViewRequestAPI):

    def get_certificate(self):
        return self.prepare_and_do_request(
            oneview_uri.CERTIFICATE_AND_KEY_URI).get('base64SSLCertData')


    def get_key(self):
        return self.prepare_and_do_request(
            oneview_uri.CERTIFICATE_AND_KEY_URI).get('base64SSLKeyData')


    def get_ca(self):
        return self.prepare_and_do_request(oneview_uri.CA_URI)


    def post_certificate(self):
        body = {'type': 'RabbitMqClientCertV2', 'commonName': 'default'}

        return self.prepare_and_do_request(oneview_uri.CERTIFICATE_RABBIT_MQ,
                                           body=body, request_type='POST')


class OneViewServerHardwareAPI(OneViewRequestAPI):

    def get_server_hardware(self, server_hardware_uri):
#       return self.prepare_and_do_request(uri)
        server_hardware_json = self.prepare_and_do_request(server_hardware_uri)
        if server_hardware_json.get("uri") is None:
            raise exception.OneViewResourceNotFoundError()

        return server_hardware_json


    def get_server_hardware_list(self):
        uri = "/rest/server-hardware?start=0&count=-1"
        server_hardwares = self.prepare_and_do_request(uri)
        return server_hardwares.get("members")

   
    def get_server_profile_assigned_to_sh(self, server_hardware_uri):
        server_hardware_json = self.get_server_hardware(server_hardware_uri)
        return server_hardware_json.get('serverProfileUri')
 

    def get_node_power_state(self, server_hardware_uri):
        power_state = self.prepare_and_do_request(uri=server_hardware_uri,
                      request_type='GET').get('powerState')
        if power_state == 'On' or power_state == 'PoweringOff':
            return states.POWER_ON
        elif power_state == 'Off' or power_state == 'PoweringOn':
            return states.POWER_OFF
        elif power_state == 'Resetting':
            return states.REBOOT
        else:
            return states.ERROR


    def parse_server_hardware_to_dict(self, server_hardware):
        port_map = server_hardware.get('portMap')
        try:
            physical_ports = port_map.get('deviceSlots')[0].get(
                                'physicalPorts')
            mac_address = physical_ports[0].get('mac')
        except Exception:
            raise Exception("Server hardware primary physical NIC not found.")
        vcpus = (server_hardware["processorCoreCount"] *
                 server_hardware["processorCount"])
        return {'name': server_hardware["name"],
                'cpus': vcpus,
                'memory_mb': server_hardware["memoryMb"],
                'local_gb': 120,
                'server_hardware_uri': server_hardware["uri"],
                'server_hardware_type_uri':
                    server_hardware["serverHardwareTypeUri"],
                'enclosure_group_uri': server_hardware['serverGroupUri'],
                'cpu_arch': 'x86_64',
                'mac': mac_address,
                'server_profile_uri': server_hardware.get('serverProfileUri')
                }


class OneViewServerProfileTemplateAPI(OneViewRequestAPI):
    def generate_server_profile_from_server_profile_template(self,
        server_profile_template_uri, server_profile_name,
        server_profile_server_hardware_uri):
        new_server_profile = self.prepare_and_do_request(
            uri=server_profile_template_uri + "/new-profile")
        new_server_profile['name'] = server_profile_name
        new_server_profile['serverHardwareUri'] = server_profile_server_hardware_uri
        return new_server_profile

    #def _assign_server_profile(self, server_profile):
    #    created_server_profile = server_profile
    #    
    #    return created_server_profile

    #def generate_and_assign_server_profile_from_server_profile_template(self,
    #    server_profile_template_uri, server_profile_name,
    #    server_profile_server_hardware_uri):
    #    pass


class OneViewServerProfileAPI(OneViewRequestAPI):
    def list(self):
        return self.prepare_and_do_request(uri=oneview_uri.SERVER_PROFILE_LIST_URI).get('members')

    def get(self, server_profile_uri):
        return self.prepare_and_do_request(uri=server_profile_uri)

    def _wait_to_assign(self, task_uri):
        max_retries=self.max_retries
        retries = 0

        task = self.prepare_and_do_request(uri=task_uri)
        while task['taskState'] != 'Completed' and retries < max_retries:
            retries += 1
            time.sleep(5)
            task = self.prepare_and_do_request(uri=task_uri)
        if task['taskState'] != 'Completed':
            raise exception.OneViewMaxRetriesExceededError(
                _("Server profile wasn't applied after %s retries.")
                % max_retries
            )
        return task

    def create(self, server_profile):
        task = self.prepare_and_do_request(uri=oneview_uri.SERVER_PROFILE_URI,
            body=server_profile,
            request_type='POST')
        task = self._wait_to_assign(task['uri'])
        return task['associatedResource']['resourceUri']

    def delete(self, server_profile_name):
        task = self.prepare_and_do_request(
            uri='/rest/server-profiles?filter=name="%s"' % (server_profile_name),
            request_type='DELETE')
        task = self._wait_to_assign(task['uri'])

    def server_profile_template_list(self):
        return [server_profile for server_profile in self.list() if server_profile.get('serverHardwareUri') is None]


    def get_server_profile_template(self, server_profile_template_uri):
        if server_profile_template_uri is None:
            raise exception.OneViewServerProfileTemplateError()

        server_profile_template_json = self.prepare_and_do_request(
            uri=server_profile_template_uri, request_type='GET'
        )

        if server_profile_template_json.get("uri") is None:
            raise exception.OneViewResourceNotFoundError()

        return server_profile_template_json


    def _build_clone_body(self, server_profile_dict, server_hardware_dict,
                          server_profile_name):
        server_profile_dict['name'] = server_profile_name
        server_profile_dict['serverHardwareUri'] = server_hardware_dict['uri']

        delete_volume_fields = ['state', 'status']
        delete_fields = ['uuid', 'modified', 'taskUri', 'eTag', 'created',
                         'serialNumber', 'inProgress', 'category', 'state',
                         'enclosureUri', 'associatedServer', 'status',
                         'enclosureBay', 'uri']

        add_volume_fields = []

        volumeAttachments = server_profile_dict["sanStorage"]["volumeAttachments"]
        for storage_information in volumeAttachments:
            volume_data = get_volume_information(storage_information["volumeUri"])
            volume_fields = {"volumeProvisionType": volume_data["provisionType"],
                             "volumeProvisionedCapacityBytes":
                                 volume_data["provisionedCapacity"],
                             "volumeShareable": volume_data["shareable"],
                             "volumeName": volume_data["deviceVolumeName"] + "-02",
                             "permanent": volume_data["isPermanent"],
                             "volumeUri": None,
                             "lun": None}
            add_volume_fields.append(volume_fields)

        len_vol_att = len(server_profile_dict["sanStorage"]["volumeAttachments"])
        for i in range(len_vol_att):
            volume_dict = server_profile_dict["sanStorage"]["volumeAttachments"][i]
            volume_dict.update(add_volume_fields[i])

        for i in delete_fields:
            del server_profile_dict[i]

        for j in range(len_vol_att):
            for i in delete_volume_fields:
                del server_profile_dict["sanStorage"]["volumeAttachments"][j][i]

        for j in range(len_vol_att):
            volume = server_profile_dict["sanStorage"]["volumeAttachments"][j]
            storage_paths = volume["storagePaths"]
            for i in range(len(storage_paths)):
                del storage_paths[i]["status"]

        connections_fields = ['id', 'name', 'functionType', 'portId',
                              'requestedMbps', 'networkUri', 'boot']
        fields_to_delete = []

        for j in range(len(server_profile_dict['connections'])):
            for i in server_profile_dict['connections'][j]:
                if not (i in connections_fields):
                    if not (i in fields_to_delete):
                        fields_to_delete.append(i)

        for j in range(len(server_profile_dict['connections'])):
            for i in fields_to_delete:
                del server_profile_dict['connections'][j][i]

        return server_profile_dict


    def clone_and_assign(self, server_hardware_uri, server_profile_template_uri,
                         node_uuid):
        max_retries=self.max_retries
        server_profile_template = self.get_server_profile_template(
                                      server_profile_template_uri)
        sh_api = OneViewServerHardwareAPI()
        server_hardware = sh_api.get_server_hardware(server_hardware_uri)
        server_profile_name = "Ironic [%s]" % (node_uuid)
        server_profile_clone_body = self._build_clone_body(server_profile_template,
                                                      server_hardware,
                                                      server_profile_name)
        ret = self.prepare_and_do_request(uri="/rest/server-profiles",
                                     body=server_profile_clone_body,
                                     request_type="POST")
        if 'taskStatus' not in ret:
            raise exception.OneViewServerProfileCloneError()
        else:
            isAssigned = False
            retries = 0
            while not isAssigned and retries < max_retries:
                retries += 1
                time.sleep(5)
                isAssigned = (sh_api.get_server_hardware(server_hardware_uri).get('state') == 'ProfileApplied')
            if not isAssigned:
                raise exception.OneViewMaxRetriesExceededError(
                    _("Server profile wasn't applied after %s retries.")
                    % max_retries
                )
        return sh_api.get_server_hardware(server_hardware_uri).get('serverProfileUri')

    def generate_and_assign_server_profile_from_server_profile_template(
        self, server_profile_template_uri, server_profile_name,
        server_profile_server_hardware_uri):
        ov_spt_api = OneViewServerProfileTemplateAPI(self.manager_url,
                                                     self.username,
                                                     self.password,
                                                     self.allow_insecure_connections,
                                                     self.tls_cacert_file)

        new_server_profile_dict = ov_spt_api.generate_server_profile_from_server_profile_template(
            server_profile_template_uri, server_profile_name,
            server_profile_server_hardware_uri)
        return self.create(new_server_profile_dict)

    def unassign_server_profile(self, server_hardware_uri, server_profile_uri):
        max_retries = self.max_retries
        sh_api = OneViewServerHardwareAPI(self.manager_url,
                                          self.username,
                                          self.password,
                                          self.allow_insecure_connections,
                                          self.tls_cacert_file)
        server_profile_body = self.prepare_and_do_request(uri=server_profile_uri)
        server_profile_body['serverHardwareUri'] = None
        server_profile_body['enclosureUri'] = None
        server_profile_body['enclosureBay'] = None
        
        self.prepare_and_do_request(uri=server_profile_uri, body=server_profile_body, request_type="PUT") 
        
        isNotAssigned = False
        retries = 0
        while not isNotAssigned and retries < max_retries:
            retries += 1
            time.sleep(5)
            isNotAssigned = (sh_api.get_server_hardware(server_hardware_uri).get('state') == 'NoProfileApplied')
        if not isNotAssigned:
            raise exception.OneViewMaxRetriesExceededError(
                _("Server profile wasn't removed successfuly after %s retries.")
                % max_retries
            )

class ResourceAPI(OneViewRequestAPI):
    def get(self, uri, field=None):
        resource = self.prepare_and_do_request(uri)
        return resource if field is None else resource[field]

    def _list(self, uri, fields=None):
        obj_list = self.prepare_and_do_request(uri).get("members")
        if fields is None:
            return obj_list

        filtered_list = []

        for obj_dict in obj_list:
            if self._is_dict_elegible(obj_dict, fields):
                filtered_list.append(obj_dict)

        return filtered_list

    def _is_dict_elegible(self, obj_dict, fields):
        for key, value in fields.items():
            if obj_dict[key] != value:
                return False
        return True

class OneViewCertificateAPI(ResourceAPI):
    def get_certificate(self):
        return self.get(oneview_uri.CERTIFICATE_AND_KEY_URI,
                        'base64SSLCertData')

    def get_key(self):
        return self.get(oneview_uri.CERTIFICATE_AND_KEY_URI,
                        'base64SSLKeyData')

    def get_ca(self):
        return self.get(oneview_uri.CA_URI)

    def post_certificate(self):
        body = {'type': 'RabbitMqClientCertV2', 'commonName': 'default'}

        return self.prepare_and_do_request(oneview_uri.CERTIFICATE_RABBIT_MQ,
                                           body=body, request_type='POST')


class OneViewServerHardwareTypeAPI(ResourceAPI):
    pass


class OneViewEnclosureGroupAPI(ResourceAPI):
    pass

#class OneViewClient:
#    def __init__(self, config):
#        self.certificate_api = OneViewCertificateAPI(config)
#        self.server_hardware_api = OneViewServerHardwareAPI(config)
#        self.server_profile_api = OneViewServerProfileAPI(config)


class OneViewClient:
    def __init__(self, manager_url, username, password,
                 allow_insecure_connections, tls_cacert_file):
        self.certificate = OneViewCertificateAPI(
            manager_url,
            username,
            password,
            allow_insecure_connections,
            tls_cacert_file
        )
        self.server_hardware = OneViewServerHardwareAPI(
            manager_url,
            username,
            password,
            allow_insecure_connections,
            tls_cacert_file
        )
        self.server_profile = OneViewServerProfileAPI(
            manager_url,
            username,
            password,
            allow_insecure_connections,
            tls_cacert_file
        )
        self.server_hardware_type = OneViewServerHardwareTypeAPI(
            manager_url,
            username,
            password,
            allow_insecure_connections,
            tls_cacert_file
        )
        self.enclosure_group = OneViewEnclosureGroupAPI(
            manager_url,
            username,
            password,
            allow_insecure_connections,
            tls_cacert_file
        )
