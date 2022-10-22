# Test using the dalybms python library to comunicate with bms over UART
# McKay Humpherys
# 9/11/2022

from dalybms import DalyBMS
import logging

logger = logging.getLogger()
bms = DalyBMS(address=8, logger=logger )
bms.connect(device="/dev/ttyAMA0")

result = bms.get_all()

print("RESULT:")
print(result)