# mqtt.py touch-gui MQTT demo.

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2024 Peter Hinch

# hardware_setup must be imported before other modules because of RAM use.
import hardware_setup  # Create a display instance
import asyncio
import gc

from gui.core.tgui import Screen, ssd
from gui.widgets import Label, Button, CloseButton, LED
from gui.core.writer import CWriter
import gui.fonts.freesans20 as font
from gui.core.colors import *

# MQTT stuff
from mqtt_as import MQTTClient, config

TOPIC = "shed"  # For demo publication and last will use same topic

# **** Start of local configuration ****
config["server"] = "192.168.0.10"  # Change to suit
#  config['server'] = 'test.mosquitto.org'

config["ssid"] = "WIFI_SSID"
config["wifi_pw"] = "WIFI PASSWORD"
# **** End of local configuration ****
config["will"] = (TOPIC, "Goodbye cruel world!", False, 0)
config["keepalive"] = 120
config["queue_len"] = 1  # Use event interface with default queue

# Set up client. Enable optional debug messages at the REPL.
MQTTClient.DEBUG = True
mqtt_started = False  # Tasks are not yet running


class BaseScreen(Screen):
    def __init__(self):
        super().__init__()
        wri = CWriter(ssd, font, GREEN, BLACK)  # Verbose
        gc.collect()
        self.outages = 0
        col = 2
        row = 2
        dc = 90
        Label(wri, row, col, "Topic")
        self.lbltopic = Label(wri, row, col + dc, 160, bdcolor=GREEN)
        self.lbltopic.value("Waiting...")
        row = 30
        Label(wri, row, col, "Message")
        self.lblmsg = Label(wri, row, col + dc, 160, bdcolor=GREEN)
        self.lblmsg.value("Waiting...")
        row = 60
        Label(wri, row + 10, col, "Network")
        self.wifi_led = LED(wri, row, col + dc, color=RED, bdcolor=WHITE)
        self.wifi_led.value(True)
        row = 100
        Label(wri, row + 10, col, "Message")
        self.msg_led = LED(wri, row, col + dc, color=BLUE, bdcolor=WHITE)
        row = 180
        Label(wri, row, col, "Publish")
        col += dc
        btn = {"height": 25, "litcolor": WHITE, "callback": self.pub}
        self.btnyes = Button(wri, row, col, text="Yes", args=("Yes",), **btn)
        col += 60
        self.btnno = Button(wri, row, col, text="No", args=("No",), **btn)
        self.wifi_state(False)
        CloseButton(wri, 30)  # Quit the application
        asyncio.create_task(self.start())

    # Callback for publish buttons
    def pub(self, button, msg):
        asyncio.create_task(self.client.publish(TOPIC, msg, qos=1))

    # Visual response to a change in WiFi state
    def wifi_state(self, up):
        self.wifi_led.color(GREEN if up else RED)
        self.btnyes.greyed_out(not up)
        self.btnno.greyed_out(not up)

    # MQTT tasks
    async def start(self):
        global mqtt_started  # Ensure that this can only run once
        if not mqtt_started:
            self.client = MQTTClient(config)
            gc.collect()
            try:
                await self.client.connect()
            except OSError:
                print("Connection failed.")
                Screen.back()  # Abort: probable MQTT or WiFi config error
            mqtt_started = True  # Next line runs forever
            await asyncio.gather(self.up(), self.down(), self.messages(), self.report())

    # Publish status report once per minute
    async def report(self):
        n = 0
        while True:
            await asyncio.sleep(60)
            n += 1
            msg = f"{n} repubs: {self.client.REPUB_COUNT} outages: {self.outages}"
            # If WiFi is down the following will pause for the duration.
            await self.client.publish(TOPIC, msg, qos=1)

    # Handle incoming messages
    async def messages(self):
        async for topic, msg, retained in self.client.queue:
            self.lbltopic.value(topic.decode())  # Show topic and message
            self.lblmsg.value(msg.decode())
            self.msg_led(True)
            await asyncio.sleep(1)  # Flash for 1s
            self.msg_led(False)

    # Starty of a WiFi outage
    async def down(self):
        while True:
            await self.client.down.wait()  # Pause until connectivity changes
            self.client.down.clear()
            self.wifi_state(False)
            self.outages += 1

    # Initial up and end of a WiFi/broker outage
    async def up(self):
        while True:
            await self.client.up.wait()
            self.client.up.clear()
            self.wifi_state(True)
            # Must re-subscribe to all topics
            await self.client.subscribe("foo_topic", 1)
            await self.client.subscribe("bar_topic", 1)


print("MQTT demo.")
Screen.change(BaseScreen)  # A class is passed here, not an instance.
