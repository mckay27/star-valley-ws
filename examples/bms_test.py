# Test using the dalybms python library to comunicate with bms over UART
# McKay Humpherys
# 9/11/2022

from dalybms import DalyBMS
import logging
import pprint

logger = logging.getLogger()
bms = DalyBMS(address=8)
bms.connect(device="/dev/ttyAMA0")

result = bms.get_all()
result2 = bms.get_cell_voltages()

print("RESULT:")
pprint.pprint(result)
pprint.pprint(result2)