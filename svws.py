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
from w1thermsensor import W1ThermSensor, Sensor, Unit, SensorNotReadyError
import board
from vedirect import VEDirect
import minimalmodbus
import RPi.GPIO as GPIO

import weewx.drivers
import weewx.units

DRIVER_NAME = "SVWS"
DRIVER_VERSION = "0.2"

# Register Units with weewx on loading
weewx.units.obs_group_dict["soilTemp_6_in"] = "group_temperature"
weewx.units.obs_group_dict["soilTemp_2_ft"] = "group_temperature"
weewx.units.obs_group_dict["soilTemp_4_ft"] = "group_temperature"
weewx.units.obs_group_dict["soilTemp_6_ft"] = "group_temperature"
weewx.units.obs_group_dict["soilTemp_8_ft"] = "group_temperature"
weewx.units.obs_group_dict["soilTemp_10_ft"] = "group_temperature"
weewx.units.obs_group_dict["bmsVoltage"] = "group_volt"
weewx.units.obs_group_dict["bmsCell1Voltage"] = "group_volt"
weewx.units.obs_group_dict["bmsCell2Voltage"] = "group_volt"
weewx.units.obs_group_dict["bmsCell3Voltage"] = "group_volt"
weewx.units.obs_group_dict["bmsCell4Voltage"] = "group_volt"
weewx.units.obs_group_dict["bmsCycles"] = "group_count"
weewx.units.obs_group_dict["bmsTemp"] = "group_temperature"
weewx.units.obs_group_dict["veBatVoltage"] = "group_volt"
weewx.units.obs_group_dict["veTotalCurrent"] = "group_amp"
weewx.units.obs_group_dict["vePanelVoltage"] = "group_volt"
weewx.units.obs_group_dict["vePanelPower"] = "group_power"
weewx.units.obs_group_dict["veMode"] = "group_index"
weewx.units.obs_group_dict["veMPPT"] = "group_index"
weewx.units.obs_group_dict["veOffReason"] = "group_index"
weewx.units.obs_group_dict["veError"] = "group_inpip dex"
weewx.units.obs_group_dict["veLoad"] = "group_boolean"
weewx.units.obs_group_dict["veLoadCurrent"] = "group_amp"
weewx.units.obs_group_dict["veYieldTotal"] = "group_energy"
weewx.units.obs_group_dict["veYieldToday"] = "group_energy"
weewx.units.obs_group_dict["veYieldYesterday"] = "group_energy"
weewx.units.obs_group_dict["veMaxPowerToday"] = "group_power"
weewx.units.obs_group_dict["veMaxPowerYesterday"] = "group_power"
weewx.units.obs_group_dict["veDaySeqNum"] = "group_count"
weewx.units.obs_group_dict["enclosureTemp"] = "group_temperature"

# Specify new unit group index
weewx.units.USUnits["group_index"] = "ind"
weewx.units.MetricUnits["group_index"] = "ind"
weewx.units.MetricWXUnits["group_index"] = "ind"

weewx.units.default_unit_format_dict["ind"] = "%.0f"
weewx.units.default_unit_label_dict["ind"] = " ind"

# Loaders
def loader(config_dict, _):
    return SVWSDriver(**config_dict[DRIVER_NAME])


def confeditor_loader():
    return SVWSConfEditor()


DEFAULT_WIND_DIR_PORT = "/dev/ttySC1"
DEFAULT_WIND_SPEED_PORT = "/dev/ttySC1"
DEFAULT_RAIN_PORT = "/dev/ttySC0"
DEFAULT_RS485_TIMEOUT = 0.1

DEFAULT_BMS_PORT = "/dev/ttyAMA0"
DEFAULT_VEDIRECT_PORT = "/dev/ttyAMA1"

TXDEN_1 = 27
TXDEN_2 = 22

TRANSMIT = GPIO.HIGH
RECV = GPIO.LOW

# Logging functions
def logmsg(level, msg):
    syslog.syslog(level, "svws: %s" % msg)


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
        self.wind_dir_addr = stn_dict.get("wind_dir_addr", None)
        self.wind_dir_port = stn_dict.get("wind_dir_port", DEFAULT_WIND_DIR_PORT)
        self.wind_speed_addr = stn_dict.get("wind_speed_addr", None)
        self.wind_speed_port = stn_dict.get("wind_speed_port", DEFAULT_WIND_SPEED_PORT)
        self.rain_addr = stn_dict.get("rain_addr", None)
        self.rain_port = stn_dict.get("rain_port", DEFAULT_RAIN_PORT)
        self.rs485_baud = stn_dict.get("rs485_baud", 9600)

        self.bms_port = stn_dict.get("bms_port", None)
        self.vedirect_port = stn_dict.get("vedirect_port", None)

        self.dht_pin = stn_dict.get("dht_pin", None)
        self.dht_tries = stn_dict.get("dht_tries", 4)

        self.enc_temp_id = stn_dict.get("enc_temp_id", None)
        self.soil_6_in_id = stn_dict.get("soil_6_in_id", None)
        self.soil_2_ft_id = stn_dict.get("soil_2_ft_id", None)
        self.soil_4_ft_id = stn_dict.get("soil_4_ft_id", None)
        self.soil_6_ft_id = stn_dict.get("soil_6_ft_id", None)
        self.soil_8_ft_id = stn_dict.get("soil_8_ft_id", None)
        self.soil_10_ft_id = stn_dict.get("soil_10_ft_id", None)

        loginf(f"Driver Version: {DRIVER_VERSION}")
        loginf(f"wind_dir_addr: {self.wind_dir_addr}")
        loginf(f"wind_dir_port: {self.wind_dir_port}")
        loginf(f"wind_speed_addr: {self.wind_speed_addr}")
        loginf(f"wind_speed_port: {self.wind_speed_port}")
        loginf(f"rain_addr: {self.rain_addr}")
        loginf(f"rain_port: {self.rain_port}")
        loginf(f"rs485_baud: {self.rs485_baud}")
        loginf(f"bms_port: {self.bms_port}")
        loginf(f"vedirect_port: {self.vedirect_port}")
        loginf(f"dht_pin: {self.dht_pin}")
        loginf(f"dht_tries: {self.dht_tries}")
        loginf(f"enc_temp_id: {self.enc_temp_id}")
        loginf(
            f"Soil Temp IDs: {self.soil_6_in_id=} {self.soil_2_ft_id=} {self.soil_4_ft_id=} {self.soil_6_ft_id=} {self.soil_8_ft_id=} {self.soil_10_ft_id=}"
        )

        # Open Modbus ports
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(TXDEN_1, GPIO.OUT)
        GPIO.setup(TXDEN_2, GPIO.OUT)
        GPIO.output(TXDEN_2, RECV)

        if self.rain_addr is not None:
            self.rain_inst = minimalmodbus.Instrument(
                self.rain_port, slaveaddress=int(self.rain_addr)
            )
            self.rain_inst.serial.baudrate = self.rs485_baud
            self.rain_inst.serial.timeout = DEFAULT_RS485_TIMEOUT

        if self.wind_dir_addr is not None:
            self.wind_dir_inst = minimalmodbus.Instrument(
                self.wind_dir_port, slaveaddress=int(self.wind_dir_addr)
            )
            self.wind_dir_inst.serial.baudrate = self.rs485_baud
            self.wind_dir_inst.serial.timeout = DEFAULT_RS485_TIMEOUT

        if self.wind_speed_addr is not None:
            self.wind_speed_inst = minimalmodbus.Instrument(
                self.wind_speed_port, slaveaddress=int(self.wind_speed_addr)
            )
            self.wind_speed_inst.serial.baudrate = self.rs485_baud
            self.wind_speed_inst.serial.timeout = DEFAULT_RS485_TIMEOUT

        # Open BMS port
        if self.bms_port is not None:
            self.bms = DalyBMS(address=8)
            try:
                self.bms.connect(self.bms_port)
                logdbg("Successfully connected to bms")
            except:
                logerr("Error connecting to bms")

        # Create DHT object
        if self.dht_pin is not None:
            self.dht = adafruit_dht.DHT22(self.dht_pin)

        # Create ds18b20 sensor objects
        if self.enc_temp_id is not None:
            self.encTemp = W1ThermSensor(
                sensor_type=Sensor.DS18B20, sensor_id=self.enc_temp_id
            )
        if self.soil_6_in_id is not None:
            self.soil_6_in = W1ThermSensor(
                sensor_type=Sensor.DS18B20, sensor_id=self.soil_6_in_id
            )
        if self.soil_2_ft_id is not None:
            self.soil_2_ft = W1ThermSensor(
                sensor_type=Sensor.DS18B20, sensor_id=self.soil_2_ft_id
            )
        if self.soil_4_ft_id is not None:
            self.soil_4_ft = W1ThermSensor(
                sensor_type=Sensor.DS18B20, sensor_id=self.soil_4_ft_id
            )
        if self.soil_6_ft_id is not None:
            self.soil_6_ft = W1ThermSensor(
                sensor_type=Sensor.DS18B20, sensor_id=self.soil_6_ft_id
            )
        if self.soil_8_ft_id is not None:
            self.soil_8_ft = W1ThermSensor(
                sensor_type=Sensor.DS18B20, sensor_id=self.soil_8_ft_id
            )
        if self.soil_10_ft_id is not None:
            self.soil_10_ft = W1ThermSensor(
                sensor_type=Sensor.DS18B20, sensor_id=self.soil_10_ft_id
            )


        # Create VEDirect reader
        if self.vedirect_port is not None:
            self.vedirect = VEDirect(self.vedirect_port)

    def getEncTemp(self):
        data = dict()

        data["enclosureTemp"] = self.encTemp.get_temperature(Unit.DEGREES_F)

        return data

    def getSoilTemp(self):
        data = dict()

        try:
            data["soilTemp_6_in"] = self.soil_6_in.get_temperature(Unit.DEGREES_F)
            data["soilTemp_2_ft"] = self.soil_2_ft.get_temperature(Unit.DEGREES_F)
            data["soilTemp_4_ft"] = self.soil_4_ft.get_temperature(Unit.DEGREES_F)
            data["soilTemp_6_ft"] = self.soil_6_ft.get_temperature(Unit.DEGREES_F)
            data["soilTemp_8_ft"] = self.soil_8_ft.get_temperature(Unit.DEGREES_F)
            data["soilTemp_10_ft"] = self.soil_10_ft.get_temperature(Unit.DEGREES_F)
        except SensorNotReadyError as err:
            logerr(f"Sensor {err.sensor.id} not ready to read")

        return data

    def getRain(self):
        data = dict()

        # Get rain since last packet
        GPIO.output(TXDEN_1, RECV)
        data["rain"] = self.rain_inst.read_register(
            0x00, number_of_decimals=1, functioncode=0x03
        )

        # Clear rain
        GPIO.output(TXDEN_1, TRANSMIT)
        self.rain_inst.write_register(0x00, value=0x5A, functioncode=6)

        return data

    def getWindDir(self):
        data = dict()

        # Get current wind direction in degrees
        time.sleep(0.1)
        data["windDir"] = self.wind_dir_inst.read_register(
            0x0000, number_of_decimals=1, functioncode=0x03
        )

        return data

    def getWindSpeed(self):
        data = dict()

        # Get current wind speed in m/s
        time.sleep(0.1)
        windSpeedMetric = self.wind_speed_inst.read_register(
            0x0000, number_of_decimals=1, functioncode=0x03
        )
        data["windSpeed"] = windSpeedMetric * 2.236936

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

        bmsResult = self.bms.get_all()
        soc = bmsResult.get("soc", None)

        if soc is not None:
            data["bmsVoltage"] = soc.get("total_voltage", None)

        bmsCellVoltages = bmsResult.get("cell_voltages", None)
        if bmsCellVoltages is not None:
            data["bmsCell1Voltage"] = bmsCellVoltages.get(1, None)
            data["bmsCell2Voltage"] = bmsCellVoltages.get(2, None)
            data["bmsCell3Voltage"] = bmsCellVoltages.get(3, None)
            data["bmsCell4Voltage"] = bmsCellVoltages.get(4, None)
        else:
            data["bmsCell1Voltage"] = None
            data["bmsCell2Voltage"] = None
            data["bmsCell3Voltage"] = None
            data["bmsCell4Voltage"] = None

        status = bmsResult.get("status", None)

        if status is not None:
            data["bmsCycles"] = status.get("cycles", None)

        bmsTemps = bmsResult.get("temperatures", None)
        bmsTemp = None
        if bmsTemps is not None:
            bmsTemp = bmsTemps.get(1, None)
        if bmsTemp is not None:
            bmsTemp = (bmsTemp * (9 / 5)) + 32

        data["bmsTemp"] = bmsTemp

        return data

    def getVE(self):
        data = dict()

        packet = self.vedirect.read_data_single()

        batV = packet.get("V", None)
        if batV is not None:
            batV = batV * 0.001

        data["veBatVoltage"] = batV

        totalCur = packet.get("I", None)
        if totalCur is not None:
            totalCur = totalCur * 0.001

        data["veTotalCurrent"] = totalCur

        panV = packet.get("VPV", None)
        if panV is not None:
            panV = panV * 0.001

        data["vePanelVoltage"] = panV
        data["vePanelPower"] = packet.get("PPV", None)
        data["veMode"] = packet.get("CS", None)
        data["veMPPT"] = packet.get("MPPT", None)
        data["veOffReason"] = packet.get("OR", None)
        data["veError"] = packet.get("ERR", None)

        load = packet.get("LOAD", None)
        if load is not None:
            if load == "ON":
                loadBool = True
            else:
                loadBool = False

            data["veLoad"] = loadBool

        loadCur = packet.get("IL", None)
        if loadCur is not None:
            loadCur = loadCur * 0.001

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

    def closePort():
        pass

    def genLoopPackets(self):

        while True:
            # Create packet
            packet = {"dateTime": int(time.time() + 0.5), "usUnits": weewx.US}

            if self.dht_pin is not None:
                packet.update(self.getDHT())
            if self.rain_addr is not None:
                packet.update(self.getRain())
            if self.wind_dir_addr is not None:
                packet.update(self.getWindDir())
            if self.wind_speed_addr is not None:
                packet.update(self.getWindSpeed())
            if self.enc_temp_id is not None:
                packet.update(self.getEncTemp())
            if None not in (
                self.soil_6_in_id,
                self.soil_2_ft_id,
                self.soil_4_ft_id,
                self.soil_6_ft_id,
                self.soil_8_ft_id,
                self.soil_10_ft_id,
            ):
                packet.update(self.getSoilTemp())
            if self.bms_port is not None:
                packet.update(self.getBMS())
            if self.vedirect_port is not None:
                packet.update(self.getVE())

            yield packet


class SVWSConfEditor(weewx.drivers.AbstractConfEditor):
    @property
    def default_stanza(self):
        return ""


if __name__ == "__main__":

    import optparse
