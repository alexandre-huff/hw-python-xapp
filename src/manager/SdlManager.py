# ==================================================================================
#
#       Copyright (c) 2020 Samsung Electronics Co., Ltd. All Rights Reserved.
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

from ricxappframe.xapp_frame import RMRXapp
from ._BaseManager import _BaseManager


class SdlManager(_BaseManager):

    def __init__(self, rmr_xapp: RMRXapp):
        super().__init__(rmr_xapp)

    def sdlGetGnbList(self):
        gnblist = self._rmr_xapp.get_list_gnb_ids()
        self.logger.info("SdlManager.sdlGetGnbList:: Processed request: {}".format(gnblist))
        return gnblist

    def sdlGetEnbList(self):
        enblist = self._rmr_xapp.get_list_enb_ids()
        self.logger.info("SdlManager.sdlGetEnbList:: Handler processed request: {}".format(enblist))
        return enblist

    def sdlGetNodeBList(self):
        nblist = self._rmr_xapp.GetListNodebIds()
        self.logger.info("SdlManager.sdlGetNodeBList:: Processed request: {}".format(nblist))
        return nblist




