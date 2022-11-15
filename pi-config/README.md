# Weewx config for SVWS

## Pip modules installed
Installed with: `sudo pip install --target=/usr/lib/python3.9 ...`

- adafruit-circuitpython-dht
- w1thermsensor
- dalybms
- vedirect-jmfife


## Modifications to dalybms to support cell voltages

Add the following at line 254 in `dalybms.py`

```
            elif status_field == 'cells':
                max_responses = 3
            elif status_field == 'temperature_sensors':
                max_responses = 3
```

Add the following at line 289 in `dalybms.py`

```
        if cell_voltages is not None:
```

Comment out self.logger.info instances