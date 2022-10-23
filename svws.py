# This is a weewx driver to enable reading from
# custom RS-485 and onewire sensors on a raspberry pi
# 
# Written by McKay Humpherys, 2022
#
# See https://github.com/mckay27/star-valley-ws for more info
#

import syslog
import time

from dalybms import DalyBMS
import adafruit_dht
from w1thermsensor import W1ThermSensor, Sensor, Unit
import board

import weewx.drivers

DRIVER_NAME = "SVWS"
DRIVER_VERSION = "0.1"


# Loaders
def loader(config_dict, _):
    return SVWSDriver(**config_dict[DRIVER_NAME])

def confeditor_loader():
    return SVWSConfEditor()

DEFAULT_WIND_DIR_PORT = "/dev/ttySC1"
DEFAULT_WIND_SPEED_PORT = "/dev/ttySC0"
DEFAULT_RAIN_PORT = "/dev/ttySC0"
DEFAULT_BMS_PORT ="/dev/ttyAMA0"


# Logging functions
def logmsg(level, msg):
    syslog.syslog(level, 'svws: %s' % msg)

def logdbg(msg):
    logmsg(syslog.LOG_DEBUG, msg)

def loginf(msg):
    logmsg(syslog.LOG_INFO, msg)

def logerr(msg):
    logmsg(syslog.LOG_ERR, msg)





class SVWSDriver(weewx.drivers.AbstractDevice):
    """weewx driver that communicates with RS-485 and one-wire sensors on a raspberry pi
    
    wind_dir_port - RS-485 port for wind direction sensor
    [Required. Default is /dev/ttySC1]
    wind_speed_port - RS-485 port for wind speed sensor
    [Required. Default is /dev/ttySC0]
    rain_port - RS-485 port for rain gauge
    [Required. Default is /dev/ttySC0]
    bms_port - Serial port for communication with DalyBMS
    [Required. Default is /dev/ttyAMA0]
    dht_pin - data pin for DHT-22 temp sensor
    [Required. Default is board.D17]
    int_temp_id - ID for ds18b20 internal to case
    [Required. Default is 0000071c9e1e]
    """
    def __init__(self, **stn_dict):
        # Read configuartion options from stn_dict and apply to self
        self.wind_dir_port = stn_dict.get('wind_dir_port', DEFAULT_WIND_DIR_PORT)
        self.wind_speed_port = stn_dict.get('wind_speed_port', DEFAULT_WIND_SPEED_PORT)
        self.rain_port = stn_dict.get('rain_port', DEFAULT_RAIN_PORT)
        self.bms_port = stn_dict.get('bms_port', DEFAULT_BMS_PORT)
        self.dht_pin = stn_dict.get('dht_pin', 17)
        self.int_temp_id = stn_dict.get('int_temp_id', "0000071c9e1e")

        loginf('driver version is %s' % DRIVER_VERSION)
        loginf('using wind_dir port %s' % self.wind_dir_port)
        loginf('using wind_speed port %s' % self.wind_speed_port)
        loginf('using rain port %s' % self.rain_port)
        loginf('using bms port %s' % self.bms_port)
        loginf('using dht data pin %s' % self.dht_pin)

        # Open RS-485 ports

        # Open BMS port
        # self.bms = DalyBMS(address=8)
        # try:
        #     self.bms.connect(self.bms_port)
        #     logdbg("Successfully connected to bms")
        # except:
        #     logerr("Error connecting to bms")

        # Create DHT object
        self.dht = adafruit_dht.DHT22(board.D17)

        # Create ds18b20 sensor objects
        self.intTemp = W1ThermSensor(sensor_type=Sensor.DS18B20, sensor_id=self.int_temp_id)
        

    def getIntTemp(self):
        data = dict()

        data["extraTemp1"] = self.intTemp.get_temperature(Unit.DEGREES_F)

        return data


    def getDHT(self):
        data = dict()
        try:
            outTemp = self.dht.temperature * (9 / 5) + 32
            outHumidity = self.dht.humidity

            data["outTemp"] = outTemp
            data["outHumidity"] = outHumidity

        except RuntimeError:
            loginf("Runtime error reading DHT22")
            data["outTemp"] = None
            data["outHumidity"] = None
    
        return data

    def getBMS(self):
        data = dict()

        bmsResult = self.bms.get_soc()

        data["consBatteryVoltage"] = bmsResult.get("total_voltage", None)

        return data

    @property
    def hardware_name(self):
        return "SVWS"


    def genLoopPackets(self):

        while True:
            # Create packet
            packet = {'dateTime': int(time.time() + 0.5),
                            'usUnits': weewx.US}

            packet.update(self.getDHT())
            packet.update(self.getIntTemp())
            # packet.update(self.getBMS())

            yield packet





class SVWSConfEditor(weewx.drivers.AbstractConfEditor):
    
    @property
    def default_stanza(self):
        return ""


if __name__ == '__main__':
    
    import optparse
