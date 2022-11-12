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
from vedirect import VEDirect

import weewx.drivers
import weewx.units

DRIVER_NAME = "SVWS"
DRIVER_VERSION = "0.1"

# Register Units with weewx on loading
weewx.units.obs_group_dict['soilTemp_6_in'] = 'group_temperature'
weewx.units.obs_group_dict['soilTemp_2_ft'] = 'group_temperature'
weewx.units.obs_group_dict['soilTemp_4_ft'] = 'group_temperature'
weewx.units.obs_group_dict['soilTemp_6_ft'] = 'group_temperature'
weewx.units.obs_group_dict['soilTemp_8_ft'] = 'group_temperature'
weewx.units.obs_group_dict['soilTemp_10_ft'] = 'group_temperature'
weewx.units.obs_group_dict['bmsVoltage'] = 'group_volt'
weewx.units.obs_group_dict['bmsCell1Voltage'] = 'group_volt'
weewx.units.obs_group_dict['bmsCell2Voltage'] = 'group_volt'
weewx.units.obs_group_dict['bmsCell3Voltage'] = 'group_volt'
weewx.units.obs_group_dict['bmsCell4Voltage'] = 'group_volt'
weewx.units.obs_group_dict['bmsCycles'] = 'group_count'
weewx.units.obs_group_dict['bmsTemp'] = 'group_temperature'
weewx.units.obs_group_dict['veBatVoltage'] = 'group_volt'
weewx.units.obs_group_dict['veTotalCurrent'] = 'group_amp'
weewx.units.obs_group_dict['vePanelVoltage'] = 'group_volt'
weewx.units.obs_group_dict['vePanelPower'] = 'group_power'
weewx.units.obs_group_dict['veMode'] = 'group_NONE'
weewx.units.obs_group_dict['veMPPT'] = 'group_NONE'
weewx.units.obs_group_dict['veOffReason'] = 'group_NONE'
weewx.units.obs_group_dict['veError'] = 'group_NONE'
weewx.units.obs_group_dict['veLoad'] = 'group_boolean'
weewx.units.obs_group_dict['veLoadCurrent'] = 'group_amp'
weewx.units.obs_group_dict['veYieldTotal'] = 'group_energy'
weewx.units.obs_group_dict['veYieldToday'] = 'group_energy'
weewx.units.obs_group_dict['veYieldYesterday'] = 'group_energy'
weewx.units.obs_group_dict['veMaxPowerToday'] = 'group_power'
weewx.units.obs_group_dict['veMaxPowerYesterday'] = 'group_power'
weewx.units.obs_group_dict['veDaySeqNum'] = 'group_count'
weewx.units.obs_group_dict['enclosureTemp'] = 'group_temperature'

# Loaders
def loader(config_dict, _):
    return SVWSDriver(**config_dict[DRIVER_NAME])

def confeditor_loader():
    return SVWSConfEditor()

DEFAULT_WIND_DIR_PORT = "/dev/ttySC1"
DEFAULT_WIND_SPEED_PORT = "/dev/ttySC0"
DEFAULT_RAIN_PORT = "/dev/ttySC0"
DEFAULT_BMS_PORT ="/dev/ttyAMA0"
DEFAULT_VEDIRECT_PORT ="/dev/ttyAMA1"


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
    enc_temp_id - ID for ds18b20 internal to enclosure
    [Required. Default is 0000071c9e1e]
    vedirect_port - Serial port for communication with SmartSolar over VE.Direct
    [Required. Default if /dev/ttyAMA1]
    """
    def __init__(self, **stn_dict):
        # Read configuartion options from stn_dict and apply to self
        self.wind_dir_port = stn_dict.get('wind_dir_port', DEFAULT_WIND_DIR_PORT)
        self.wind_speed_port = stn_dict.get('wind_speed_port', DEFAULT_WIND_SPEED_PORT)
        self.rain_port = stn_dict.get('rain_port', DEFAULT_RAIN_PORT)
        self.bms_port = stn_dict.get('bms_port', DEFAULT_BMS_PORT)
        self.dht_pin = stn_dict.get('dht_pin', board.D17)
        self.dht_tries = stn_dict.get('dht_tries', 4)
        self.enc_temp_id = stn_dict.get('int_temp_id', "0000071c9e1e")
        self.vedirect_port = stn_dict.get('vedirect_port', DEFAULT_VEDIRECT_PORT)

        loginf('driver version is %s' % DRIVER_VERSION)
        loginf('using wind_dir port %s' % self.wind_dir_port)
        loginf('using wind_speed port %s' % self.wind_speed_port)
        loginf('using rain port %s' % self.rain_port)
        loginf('using bms port %s' % self.bms_port)
        loginf('using dht data pin %s' % self.dht_pin)
        loginf('using vedirect port %s' % self.vedirect_port)

        # Open RS-485 ports

        # Open BMS port
        self.bms = DalyBMS(address=8)
        try:
            self.bms.connect(self.bms_port)
            logdbg("Successfully connected to bms")
        except:
            logerr("Error connecting to bms")

        # Create DHT object
        self.dht = adafruit_dht.DHT22(self.dht_pin)

        # Create ds18b20 sensor objects
        self.encTemp = W1ThermSensor(sensor_type=Sensor.DS18B20, sensor_id=self.enc_temp_id)

        # Create VEDirect reader
        self.vedirect = VEDirect(self.vedirect_port)
        

    def getEncTemp(self):
        data = dict()

        data["enclosureTemp"] = self.encTemp.get_temperature(Unit.DEGREES_F)

        return data


    def getDHT(self):
        data = dict()

        curTry = 0
        while curTry < self.dht_tries:
            try:
                outTemp = self.dht.temperature * (9 / 5) + 32
                outHumidity = self.dht.humidity

                data["outTemp"] = outTemp
                data["outHumidity"] = outHumidity
                break

            except RuntimeError:
                loginf("Runtime error reading DHT22")
                data["outTemp"] = None
                data["outHumidity"] = None
    
        return data

    def getBMS(self):
        data = dict()

        bmsResult = self.bms.get_soc()

        data["bmsVoltage"] = bmsResult.get("total_voltage", None)

        bmsCellVoltages = bmsResult.get("cell_voltages", None)
        if bmsCellVoltages is not None:
            data["bmsCell1Voltage"] = bmsCellVoltages.get("1", None)
            data["bmsCell2Voltage"] = bmsCellVoltages.get("2", None)
            data["bmsCell3Voltage"] = bmsCellVoltages.get("3", None)
            data["bmsCell4Voltage"] = bmsCellVoltages.get("4", None)
        else:
            data["bmsCell1Voltage"] = None
            data["bmsCell2Voltage"] = None
            data["bmsCell3Voltage"] = None
            data["bmsCell4Voltage"] = None

        data["bmsCycles"] = bmsResult.get("cycles", None)

        bmsTemp = bmsResult.get("temperatures", None)
        if bmsTemp is not None:
            bmsTemp = (bmsTemp * (9 / 5)) + 32

        data["bmsTemp"] = bmsTemp

        return data

    def getVE(self):
        data = dict()

        packet = self.vedirect.read_data_single()

        batV = packet.get("V", None)
        if batV is not None:
            batV = batV * .001

        data["veBatVoltage"] = batV

        totalCur = packet.get("I", None)
        if totalCur is not None:
            totalCur = totalCur * .001

        data["veTotalCurrent"] = totalCur

        panV = packet.get("VPV", None)
        if panV is not None:
            panV = panV * .001

        data["vePanelVoltage"] = panV
        data["vePanelPower"] = packet.get("PPV", None)
        data["veMode"] = VEDirect.device_state_map.get(str(packet.get("CS", None)), None)
        data["veMPPT"] = VEDirect.trackerModeDecode.get(packet.get("MPPT", None), None)
        data["veOffReason"] = VEDirect.offReasonDecode.get(packet.get("OR", None), None)
        data["veError"] = VEDirect.error_codes.get(packet.get("ERR", None), None)

        load = packet.get("LOAD", None)
        if load is not None:
            if load == "ON":
                loadBool = True
            else:
                loadBool = False

        data["veLoad"] = loadBool

        loadCur = packet.get("IL", None)
        if loadCur is not None:
            loadCur = loadCur * .001

        data["veLoadCurrent"] = loadCur

        yieldTot = packet.get("H19", None)
        if yieldTot is not None:
            yieldTot = yieldTot * 10

        data["veYieldTotal"] = yieldTot

        yieldToday = packet.get("H20", None)
        if yieldToday is not None:
            yieldToday = yieldToday * 10

        data["veYieldToday"] = yieldToday

        yieldYesterday = packet.get("H22", None)
        if yieldYesterday is not None:
            yieldYesterday = yieldYesterday * 10

        data["veYieldYesterday"] = yieldYesterday
        data["veMaxPowerToday"] = packet.get("H21", None)
        data["veMaxPowerYesterday"] = packet.get("H23", None)
        data["veDaySeqNum"] = packet.get("HSDS", None)

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
            packet.update(self.getEncTemp())
            packet.update(self.getBMS())
            packet.update(self.getVE())

            yield packet





class SVWSConfEditor(weewx.drivers.AbstractConfEditor):
    
    @property
    def default_stanza(self):
        return ""


if __name__ == '__main__':
    
    import optparse
