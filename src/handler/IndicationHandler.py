# ==================================================================================
#
#       Copyright (c) 2024 Alexandre Huff. All Rights Reserved.
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
Handles indication messages from enbs and gnbs through rmr.
"""

from ricxappframe.xapp_frame import RMRXapp, rmr
from ._BaseHandler import _BaseHandler

from pycrate_asn1rt.err import ASN1ObjErr, ASN1Err
from ..asn1.e2ap import E2AP_PDU_Descriptions
from ..asn1.kpm import E2SM_KPM_IEs


class IndicationHandler(_BaseHandler):

    def __init__(self, rmr_xapp: RMRXapp, msgtype):
        super().__init__(rmr_xapp, msgtype)


    def request_handler(self, rmr_xapp, summary, sbuf):
        """
            Handles indication messages.

            Parameters
            ----------
            rmr_xapp: rmr Instance Context

            summary: dict (required)
                buffer content

            sbuf: str (required)
                length of the message
        """

        raw_data = summary[rmr.RMR_MS_PAYLOAD]
        self.logger.debug("IndicationHandler.request_handler:: Handler processing indication request")

        e2ap_pdu = E2AP_PDU_Descriptions.E2AP_PDU
        try:
            e2ap_pdu.from_aper(raw_data)    # raises ASN1ObjErr
            pdu = e2ap_pdu.get_val()
            self.logger.debug(f"E2AP Indication PDU is {pdu}")

            if pdu[0] == 'initiatingMessage':
                ies = e2ap_pdu.get_val_at(['initiatingMessage', 'value', 'RICindication', 'protocolIEs'])   # raises ASN1Err
                for ie in ies:
                    if ie['value'][0] == 'RICindicationHeader':
                        self.process_indication_header(ie['value'][1])

                    elif ie['value'][0] == 'RICindicationMessage':
                        self.process_indication_message(ie['value'][1])

            else:
                self.logger.error(f"Expecting PDU initiatingMessage, but got {pdu[0]}")

        except ASN1ObjErr as ex:
                self.logger.error(f"Unable to decode E2AP Indication. Reason: {type(ex).__name__} - {ex}")
        except ASN1Err as ex:
                self.logger.error(f"Unable to process E2AP Indication data. Reason: {type(ex).__name__} - {ex} in PDU {pdu}")

        finally:
            self._rmr_xapp.rmr_free(sbuf)

    def process_indication_header(self, header_bytes):
        self.logger.debug("Processing RIC Indication Header")
        header = E2SM_KPM_IEs.E2SM_KPM_IndicationHeader
        try:
            header.from_aper(header_bytes)  # raises ASN1ObjErr
            data = header.get_val_at(['indicationHeader-formats', 'indicationHeader-Format1'])  # raises ASN1Err
            self.logger.info(f"KPM Indication Header is {data}")

        except ASN1ObjErr as ex:
            self.logger.error(f"Unable to decode E2AP Indication Header. Reason: {type(ex).__name__} - {ex}")
        except ASN1Err as ex:
            self.logger.error(f"Unable to process KPM Indication Header. Reason: {type(ex).__name__} - {ex} in Header {header.get_val()}")

    def process_indication_message(self, message_bytes):
        self.logger.debug("Processing RIC Indication Message")
        message = E2SM_KPM_IEs.E2SM_KPM_IndicationMessage

        try:
            message.from_aper(message_bytes)  # raises ASN1ObjErr
            data = message.get_val_at(['indicationMessage-formats', 'indicationMessage-Format1'])   # raises ASN1Err
            self.logger.info(f"KPM Indication Message is {data}")

        except ASN1ObjErr as ex:
            self.logger.error(f"Unable to decode E2AP Indication Message. Reason: {type(ex).__name__} - {ex}")
        except ASN1Err as ex:
            self.logger.error(f"Unable to process KPM Indication Message. Reason: {type(ex).__name__} - {ex} in Message {message.get_val()}")
