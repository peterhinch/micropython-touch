# ili9488_xpt2046_esp32s3.py Customise for your hardware config

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2025 Peter Hinch

# As written, supports:
# ili9488 320x480 displays on ESP32S3.
# XPT2046 touch controller.
# Edit the driver import for other displays.

# Demo of initialisation procedure designed to minimise risk of memory fail
# when instantiating the frame buffer. The aim is to do this as early as
# possible before importing other modules.

# WIRING Pinouts for UM Feather S3
# Pico      Display
# GPIO Pin
# 3v3   2   Vin, LED
# IO36 11   CLK  Hardware SPI0
# IO35 12   DATA (AKA SI MOSI)
# IO18  6   Rst
# IO17  5   DC
# Gnd   4   Gnd
# IO14  7   CS
# IO12  8   Touch SDA MISO
# IO6   9   Touch MOSI
# IO5  10   Touch CS
# IO8  17   Touch scl

from machine import Pin, SoftSPI, SPI, freq
import gc
from drivers.ili94xx.ili9488 import ILI9488 as SSD

# Create and export an SSD instance
prst = Pin(18, Pin.OUT, value=1)
pdc = Pin(17, Pin.OUT, value=0)  # Arbitrary pins
pcs = Pin(14, Pin.OUT, value=1)
# 24MHz actual. This is an overclock: 20MHz is datasheet max, but ask for that and you get 12MHz.
spi = SPI(1, sck=Pin(36), mosi=Pin(35), miso=Pin(37), baudrate=24_000_000)
gc.collect()  # Precaution before instantiating framebuf
ssd = SSD(spi, pcs, pdc, prst)  # 320x480 default
from gui.core.tgui import Display, quiet

# quiet()  # Comment this out for periodic free RAM messages

# Touch configuration
from touch.xpt2046 import XPT2046

spi = SoftSPI(mosi=Pin(6), miso=Pin(12), sck=Pin(8))  # 2.5MHz max
tpad = XPT2046(spi, Pin(5, Pin.OUT, value=1), ssd)
# To create a tpad.init line for your displays please read SETUP.md
tpad.init(480, 320, 139, 198, 3981, 3915, False, True, True)  # Landscape
# tpad.init(480, 320, 160, 165, 4002, 3933, True, True, False)  # Portrait
display = Display(ssd, tpad)
