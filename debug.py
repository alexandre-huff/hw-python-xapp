# ==================================================================================
#
#       Copyright (c) 2024 Alexandre Huff
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

# This file is intended just to run this project in vscode. Should not appear in official repo. :-)

import signal
from src.hwxapp import HWXapp


def launchXapp():
    hwxapp = HWXapp()
    hwxapp.start(True)

    signum = signal.sigwait((signal.SIGINT, signal.SIGTERM))
    print(f'Signal handler called with signal {signal.Signals(signum).name} ({signum})')

    hwxapp.stop()


if __name__ == "__main__":
    launchXapp()
