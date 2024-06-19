# ==================================================================================
#
#       Copyright (c) 2021 Samsung Electronics Co., Ltd. All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#          http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ==================================================================================
"""

"""

import os
import requests
from ricxappframe.xapp_frame import RMRXapp
from ricxappframe.xapp_subscribe import NewSubscriber
from ricxappframe.xapp_rest import initResponse
from ricxappframe.util.constants import Constants as FrameConstants
import json
from ..utils.constants import Constants
from ._BaseManager import _BaseManager
from mdclogpy.Logger import Level

from ..asn1.kpm import *

class SubscriptionManager(_BaseManager):

    __namespace = "e2Manager"

    def __init__(self, rmr_xapp: RMRXapp):
        super().__init__(rmr_xapp)

        config = self._rmr_xapp._config_data
        try:
            ports = config['messaging']['ports']
            for port in ports:
                if port['name'] == 'http':
                    self.http_port = port['port']
                elif port['name'] == 'rmrroute':
                    self.rmrroute_port = port['port']
                elif port['name'] == 'rmrdata':
                    self.rmrdata_port = port['port']

        except KeyError as err:
            self.logger.warning(f"Key not found in xapp descriptor file: {err}")

        if not hasattr(self, 'http_port'):
            self.http_port = Constants.DEFAULT_HTTP_PORT
            self.logger.warning(f"Using default http port number {self.http_port}")

        if not hasattr(self, 'rmrroute_port'):
            self.rmrroute_port = Constants.DEFAULT_RMRROUTE_PORT
            self.logger.warning(f"Using default rmrroute port number {self.rmrroute_port}")

        if not hasattr(self, 'rmrdata_port'):
            self.rmrdata_port = Constants.DEFAULT_RMRDATA_PORT
            self.logger.warning(f"Using default rmrdata port number {self.rmrdata_port}")


        url = Constants.SUBSCRIPTION_PATH.format(Constants.PLT_NAMESPACE,
                                                 Constants.SUBSCRIPTION_SERVICE,
                                                 Constants.PLT_NAMESPACE,
                                                 Constants.SUBSCRIPTION_PORT,
                                                 "/ric/v1")
        self._submgr = NewSubscriber(uri=url, local_port=self.http_port, rmr_port=self.rmrroute_port)
        self._submgr.ResponseHandler(responseCB=self._subscriptionPostHandler)
        self._subscriptions = []

    def get_gnb_list(self):
        gnblist = self._rmr_xapp.get_list_gnb_ids()   # yet to come in library
        self.logger.info("SubscriptionManager.getGnbList:: Processed request: {}".format(gnblist))
        return gnblist

    def get_enb_list(self):
        enblist = self._rmr_xapp.get_list_enb_ids()   # yet to come in library
        self.logger.info("SubscriptionManager.sdlGetGnbList:: Handler processed request: {}".format(enblist))
        return enblist

    def _create_subscription_request_payload(self, meid):
        hostname = os.environ.get("HOSTNAME")
        http_addr = "service-{}-{}-http.{}".format(FrameConstants.DEFAULT_XAPP_NS,
                                                hostname,
                                                FrameConstants.DEFAULT_XAPP_NS)
        triggers = self._build_event_trigger_definition_format1()
        action = self._build_action_definition_format1()

        payload = {
            "SubscriptionId": "",
            "ClientEndpoint": {
                "Host": http_addr,
                "HTTPPort": self.http_port,
                "RMRPort": self.rmrdata_port
            },
            "Meid": meid,
            "RANFunctionID": 0,
            "SubscriptionDetails": [{
                "XappEventInstanceId": 12345,
                # "EventTriggers": [1],
                "EventTriggers": triggers,
                "ActionToBeSetupList": [{
                    "ActionID": 0,
                    "ActionType": Constants.ACTION_TYPE,
                    # "ActionDefinition": [1],
                    "ActionDefinition": action,
                    "SubsequentAction": {
                        "SubsequentActionType": "continue",
                        "TimeToWait": "zero"
                    }
                }]
            }]
        }

        return payload

    def send_subscription_request(self, meid):
        subscription_request = self._create_subscription_request_payload(meid)
        self.logger.info("Subscription payload is {}".format(subscription_request))

        url = Constants.SUBSCRIPTION_PATH.format(Constants.PLT_NAMESPACE,
                                                 Constants.SUBSCRIPTION_SERVICE,
                                                 Constants.PLT_NAMESPACE,
                                                 Constants.SUBSCRIPTION_PORT,
                                                 Constants.SUBSCRIPTION_RESOURCE)
        try:
            response = requests.post(url, json=subscription_request)
            response.raise_for_status()
            if response.status_code == 201:
                data = response.json()
                sub_id = data['SubscriptionId']
                self.logger.debug("Subscription Request returned status={}, data={}".format(response.status_code, data))
                self._subscriptions.append(sub_id)
            else:
                self.logger.debug("Subscription Request returned status={}, reason={}, data={}".format(response.status_code, response.reason, response.content))

        except requests.exceptions.HTTPError as err_h:
            self.logger.error("An Http Error occurred: {}".format(repr(err_h)))
        except requests.exceptions.ConnectionError as err_c:
            self.logger.error("An Error Connecting to the API occurred: {}".format(repr(err_c)))
        except requests.exceptions.Timeout as err_t:
            self.logger.error("A Timeout Error occurred: {}".format(repr(err_t)))
        except requests.exceptions.JSONDecodeError as err_j:
            self.logger.error("A JSON Error occurred: {}".format(repr(err_j)))
        except requests.exceptions.RequestException as err:
            self.logger.error("An Unknown Error occurred: {}".format(repr(err)))
        except KeyError as err_k:
            self.logger.error("Key not found in Subscription Response: {}".format(repr(err_k)))

############ New Subscription implementation based on xappframe #############
################### It will replace all the above send_subscription_request method ###################

    def subscribe(self, meid):
        hostname = os.environ.get("HOSTNAME")
        host = "http://service-{}-{}-http.{}".format(FrameConstants.DEFAULT_XAPP_NS,
                                                hostname,
                                                FrameConstants.DEFAULT_XAPP_NS)
        http_port = self.http_port
        rmr_port = self.rmrdata_port
        ran_func_id = 0

        event_triggers = self._build_event_trigger_definition_format1()
        action_definition = self._build_action_definition_format1()

        client_ep = self._submgr.SubscriptionParamsClientEndpoint(host, http_port, rmr_port)

        subs_action = self._submgr.SubsequentAction("continue", "zero")
        action = self._submgr.ActionToBeSetup(0, "report", action_definition, subs_action)
        actions = []
        actions.append(action)
        details = self._submgr.SubscriptionDetail(12345, event_triggers, actions)
        sub_parms = self._submgr.SubscriptionParams("", client_ep, meid, ran_func_id, None, subscription_details=details)

        sdict = sub_parms.to_dict()
        jdump = json.dumps(sdict, indent=2)
        print(jdump)
        data, reason, status = self._submgr.Subscribe(sub_parms)
        self.logger.debug("Subscription Request returned status={}, reason={}, data={}".format(status, reason, json.loads(data)))

    def unsubscribe(self):
        for sub_id in self._subscriptions:
            data, reason, status = self._submgr.UnSubscribe(sub_id)
            if status == 204:
                self.logger.debug("Subscription Delete returned status={}".format(status))
            else:
                self.logger.debug("Subscription Delete returned status={}, reason={}, data={}".format(status, reason, data))

    def _subscriptionPostHandler(self, name, path, data, ctype):
        """
        _subscriptionPostHandler
            process Subsctiption Manager requests
        """
        self.logger.debug("_subscriptionPostHandler has been called")
        response = initResponse()
        return response

    def _build_event_trigger_definition_format1(self):
        """
            Builds an ASN1-based event trigger definition format 1
            Returns a list of integers that represents the ASN1-encoded trigger definition
        """
        period = dict(reportingPeriod=1000)    # 1 second
        def_fmt1 = tuple(('eventDefinition-Format1', period))
        def_formats = dict()
        def_formats['eventDefinition-formats'] = def_fmt1

        trigger = E2SM_KPM_IEs.E2SM_KPM_EventTriggerDefinition
        trigger.set_val(def_formats)

        if self.logger.get_level() == Level.DEBUG:
            print("KPM Event Trigger Definition is ", trigger.to_asn1())

        encoded = trigger.to_aper()
        enc_bytes = list(encoded)

        return enc_bytes

    def _build_action_definition_format1(self):
        """
            Builds an ASN1-based action definition format 1
            Returns a list of integers that represents the ASN1-encoded action definition
        """
        metrics = [
            "DRB.RlcSduTransmittedVolumeDL-Filter",
            "DRB.RlcSduTransmittedVolumeUL-Filter",
            "DRB.PerDataVolumeDLDist.Bin ",
            "DRB.PerDataVolumeULDist.Bin",
            "DRB.RlcPacketDropRateDLDist",
            "DRB.PacketLossRateULDist",
            "L1M.DL-SS-RSRP.SSB",
            "L1M.DL-SS-SINR.SSB",
            "L1M.UL-SRS-RSRP"
        ]

        action_fmt1 = dict()
        action_formats = tuple(('actionDefinition-Format1', action_fmt1))

        action_definition = dict()
        action_definition['ric-Style-Type'] = 1
        action_definition['actionDefinition-formats'] = action_formats

        measInfoList = list()
        action_fmt1['measInfoList'] = measInfoList
        action_fmt1['granulPeriod'] = 1000  # 1 second

        for metric in metrics:
            measInfoItem = dict()
            labelInfoList = list()

            measInfoItem['measType'] = tuple(('measName', metric))
            measInfoItem['labelInfoList'] = labelInfoList

            noLabel = dict(noLabel='true')
            labelInfoItem = dict(measLabel=noLabel)
            labelInfoList.append(labelInfoItem)

            measInfoList.append(measInfoItem)

        action = E2SM_KPM_IEs.E2SM_KPM_ActionDefinition
        action.set_val(action_definition)

        if self.logger.get_level() == Level.DEBUG:
            print("KPM Action Definition is " ,action.to_asn1())

        encoded = action.to_aper()
        enc_bytes = list(encoded)

        return enc_bytes
