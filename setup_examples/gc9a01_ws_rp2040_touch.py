# gc9a01_ws_rp2040_touch.py
# Driver for https://www.waveshare.com/wiki/RP2040-Touch-LCD-1.28
# Also https://www.waveshare.com/RP2350-LCD-1.28.htm tested by Adam Knowles

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2024 Peter Hinch

# Pinout (from Waveshare schematic)
# Touch Controller
# I2C SDA 6
# I2C CLK 7
# TP RST 22
# TP INT 21

# LCD
# DC 8
# CS 9
# SCK 10
# MOSI 11
# MISO 12
# RST 13
# BL 25


import gc
from machine import Pin, SPI, I2C
from drivers.gc9a01.gc9a01 import GC9A01 as SSD

# May use either driver.
# from drivers.gc9a01.gc9a01_8_bit import GC9A01 as SSD

pdc = Pin(8, Pin.OUT, value=0)
pcs = Pin(9, Pin.OUT, value=1)
prst = Pin(13, Pin.OUT, value=1)
pbl = Pin(25, Pin.OUT, value=1)

gc.collect()  # Precaution before instantiating framebuf

# Define the display
# gc9a01 datasheet allows <= 100MHz
spi = SPI(1, 33_000_000, sck=Pin(10), mosi=Pin(11), miso=Pin(12))
ssd = SSD(spi, pcs, pdc, prst)  # Bool options lscape, usd, mirror
from gui.core.tgui import Display, quiet

quiet()  # Comment this out for periodic free RAM messages

# Touch configuration.
from touch.cst816s import CST816S

pint = Pin(21, Pin.IN)  # Touch interrupt
ptrst = Pin(22, Pin.OUT, value=1)  # Touch reset
i2c = I2C(1, scl=Pin(7), sda=Pin(6), freq=100_000)
tpad = CST816S(i2c, ptrst, pint, ssd)
# To create a tpad.init line for your displays please read SETUP.md
# The following is consistent with the SSD constructor args above.
tpad.init(240, 240, 0, 0, 240, 240, False, True, True)
display = Display(ssd, tpad)
