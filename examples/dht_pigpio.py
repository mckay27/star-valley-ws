from .DHT22 import sensor as DHT22
import examples.pigpio as pigpio

dht = DHT22(pi=pigpio.pi(), gpio=17)

outTemp = dht.temperature() * (9/5) + 32
outHumidity = dht.humidity()

print(outTemp)
print(outHumidity)