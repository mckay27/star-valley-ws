import minimalmodbus
import time
import RPi.GPIO as GPIO
import serial

TXDEN_1 = 27
TXDEN_2 = 22

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(TXDEN_1, GPIO.OUT)
GPIO.setup(TXDEN_2, GPIO.OUT)

GPIO.output(TXDEN_1, GPIO.LOW)  
GPIO.output(TXDEN_2, GPIO.LOW)   

instrument = minimalmodbus.Instrument("/dev/ttySC1", slaveaddress=0x02)
instrument1 = minimalmodbus.Instrument("/dev/ttySC1", slaveaddress=0x03)

instrument.serial.baudrate = 9600
instrument.serial.timeout = .1
instrument1.serial.baudrate = 9600
instrument1.serial.timeout = .1

wind_dir = instrument.read_register(0x0000, number_of_decimals=1, functioncode=0x03)
print("Wind Dir: " + str(wind_dir))
time.sleep(.1)
wind_dir = instrument1.read_register(0x0000, number_of_decimals=1, functioncode=0x03)
print("Wind Speed: " + str(wind_dir))

# ser = serial.Serial("/dev/ttySC0", baudrate=9600, timeout=5, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
# ser.write(serial.to_bytes([0xFF,0x03,0x07,0xD0,0x00,0x01,0x91,0x59]))
# resp = ser.read(7)
# print(resp)
# print(resp.hex())

