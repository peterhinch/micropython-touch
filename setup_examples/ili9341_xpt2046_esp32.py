# ili9341_xpt2046_esp32.py

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2024 Peter Hinch

# Tested on eBay sourced display

# Demo of initialisation procedure designed to minimise risk of memory fail
# when instantiating the frame buffer. The aim is to do this as early as
# possible before importing other modules.

# WIRING for Feather S3
# Attempt to use a shared SPI bus to save pins failed with a single touch registering
# as multiple. Perhaps bus clock rate switching only works on bare metal hosts?

# LCD       picoW (GPIO)
# VCC       Vin
# GND       Gnd
# LCD_DC    9
# LCD_CS    38
# LCD_CLK   36
# MOSI      35
# MISO      37
# BackLight 3V3
# LCD_RST   33
# (Touch)
# TP_CS     8
# MOSI      11
# MISO      10
# SCK       7

from machine import Pin, SPI, SoftSPI
import gc
from drivers.ili93xx.ili9341 import ILI9341 as SSD


# Screen configuration
# (Create and export an SSD instance)
prst = Pin(33, Pin.OUT, value=1)
pdc = Pin(9, Pin.OUT, value=0)
pcs = Pin(38, Pin.OUT, value=1)

# Use hardSPI (bus 1)
spi = SPI(1, 33_000_000, sck=Pin(36), mosi=Pin(35), miso=Pin(37))
# Precaution before instantiating framebuf
gc.collect()
ssd = SSD(spi, height=240, width=320, dc=pdc, cs=pcs, rst=prst, usd=True)
from gui.core.tgui import Display, quiet

# quiet()  # Comment this out for periodic free RAM messages
from touch.xpt2046 import XPT2046

# Touch configuration
sspi = SoftSPI(mosi=Pin(11), miso=Pin(10), sck=Pin(7))  # 2.5MHz max

tpad = XPT2046(sspi, Pin(8, Pin.OUT, value=1), ssd)
# To create a tpad.init line for your displays please read SETUP.md
# tpad.init(240, 320, 151, 151, 4095, 4095, True, True, True)

# instantiate a Display
display = Display(ssd, tpad)
