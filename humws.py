#!/usr/bin/env python
# McKay Humpherys 2022

"""Driver for collecting data from custom weatherstation

Future info about device to go here
"""
from asyncio.windows_events import NULL
import sys
sys.path.insert(0, '/home/mckay/Documents/weewx/bin')

import minimalmodbus
import weewx
import weewx.drivers
from weewx.wxformulas import calculate_rain

DRIVER_NAME = 'HUMWS'
DRIVER_VERSION = '0.1'


class HUMWSDriver(weewx.drivers.AbstractDevice):

    def hardware_name(self):
        return 'HUMPHERYS WS'

    def genLoopPackets(self):
        
        return NULL