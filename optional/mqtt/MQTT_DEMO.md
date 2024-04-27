# The MQTT demo

This demo displays incoming MQTT messages as they arrive. Two `Button` widgets
each cause a message to be published. The demo `mqtt.py` will need to be edited
for local conditions. As a minimum the following lines will need to be adapted:
```Python
config["server"] = "192.168.0.10"  # Change to suit
#  config['server'] = 'test.mosquitto.org'

config["ssid"] = "WIFI_SSID"
config["wifi_pw"] = "WIFI PASSWORD"
```
The demo has high RAM requirements: the ideal host is an ESP32 with SPIRAM. On
such a host the files `mqtt.py` and `mqtt_as.py` should be copied to the root
directory of the host. On a Pico W the demo has run without using frozen
bytecode but `mqtt_as.py` was precompiled with `mqtt_as.mpy` being copied to the
host. Ideally the GUI and `mqtt_as.py` should be frozen, with `mqtt.py` put in
the root directory for easy modification.

# Resources

Documentation on [mqtt_as](https://github.com/peterhinch/micropython-mqtt/blob/master/mqtt_as/README.md).  
Latest [mqtt_as.py](https://github.com/peterhinch/micropython-mqtt/blob/master/mqtt_as/mqtt_as.py).  
[Mosquitto](https://mosquitto.org/) An excellent broker, plus test utilities
`mosquitto_pub` and `mosquitto_sub`.

# Running the demo

Ensure that the touch screen has been correctly configured and can run at least
one of the standard demos.

The demo is started with
```Python
>>> import mqtt
```
The script publishes to the topic "shed": a status report every 60s plus a
message every time the "Yes" or "No" button is pressed. Buttons are disabled if
connectivity to the broker is unavailable. Publications can be checked with:
```bash
$ mosquitto_sub -h 192.168.0.10 -t "shed"
```
The demo subscribes to two topics, "foo_topic" and "bar_topic". Repetitive
publications to these topics can be triggered with the `pubtest` bash script:
```bash
$ ./pubtest
```
Note that this script assumes a broker on `192.168.0.10`: edit as necessary.
Individual messages may be sent with (for example)
```bash
$ mosquitto_pub -h 192.168.0.10 -t bar_topic -m "bar message" -q 1
```
The "Network" LED widget shows red on a WiFi or broker outage, green normally.  
The "Message" LED pulses blue each time a message is received.

# Connectivity

If `mqtt_as` is unable to establish an initial connection to the broker the
application quits with an error message. After successful connection, subsequent
outages are handled automatically. This is by design: failure to establish an
initial connection is usually because configuration values such as WiFi
credentials or broker address are incorrect.
