# star-valley-ws

This project is a driver for [weewx](weewx.com) that works with RS-485 weather sensors purchased from Aliexpress.

## Physical sensors

### Wind direction

The RS-485 version of [this](https://www.aliexpress.com/item/2251800633257050.html?spm=a2g0o.cart.0.0.5d5538daWXKizm&mp=1) sensor is what this driver was written for.

### Wind speed

The RS-485 version of [this](https://www.aliexpress.com/item/2251832771249627.html?spm=a2g0o.cart.0.0.5d5538daWXKizm&mp=1) sensor is what this driver was written for.

### Rainfall

The RS-485 version of [this](https://www.aliexpress.com/item/3256804246014341.html?spm=a2g0o.cart.0.0.5d5538daWXKizm&mp=1) sensor is what this driver was written for.

### Outside Temperature

[This](https://www.aliexpress.com/item/2251832679343807.html?spm=a2g0o.cart.0.0.5d5538daWXKizm&mp=1) AM2306 sensor, which is a DHT22, is what this driver was written for.

## SVWS weewx driver

### Config Options
- wind_dir_port - RS-485 port for wind direction sensor [Required. Default is /dev/ttySC1]
- wind_speed_port - RS-485 port for wind speed sensor [Required. Default is /dev/ttySC0]
- rain_port - RS-485 port for rain gauge [Required. Default is /dev/ttySC0]
- bms_port - Serial port for communication with DalyBMS [Required. Default is /dev/ttyAMA0]
- dht_pin - data pin for DHT-22 temp sensor [Required. Default is board.D17]
- int_temp_id - ID for ds18b20 internal to case [Required. Default is 0000071c9e1e]