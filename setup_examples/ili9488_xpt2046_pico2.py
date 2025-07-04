# ili9488_xpt2046_pico2.py Customise for your hardware config

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2025 Peter Hinch

# This driver is for pure ILI9488 hardware (see note on ili9488_ws_pico_res_touch.py).

# As written, supports:
# ili9488 320x480 displays on Pi Pico2. (Pico: overclock to 250MHz).
# XPT2046 touch controller.
# Edit the driver import for other displays.

# Demo of initialisation procedure designed to minimise risk of memory fail
# when instantiating the frame buffer. The aim is to do this as early as
# possible before importing other modules.

# WIRING
# Pico      Display
# GPIO Pin
# 3v3  36   Vin
# IO6   9   CLK  Hardware SPI0
# IO7  10   DATA (AKA SI MOSI)
# IO9  12   Rst
# IO8  11   DC
# Gnd  13   Gnd
# IO10 14   CS
# IO12 16   Touch SDA MISO
# IO13 17   Touch MOSI
# IO14 19   Touch CS
# IO15 20   Touch scl

from machine import Pin, SoftSPI, SPI, freq
import gc
from drivers.ili94xx.ili9488 import ILI9488 as SSD

freq(300_000_000)  # RP2 V2 overclock
# Create and export an SSD instance
prst = Pin(9, Pin.OUT, value=1)
pdc = Pin(8, Pin.OUT, value=0)  # Arbitrary pins
pcs = Pin(10, Pin.OUT, value=1)
# 24MHz actual. This is an overclock: 20MHz is datasheet max, but ask for that and you get 12MHz.
spi = SPI(0, sck=Pin(6), mosi=Pin(7), miso=Pin(4), baudrate=24_000_000)
gc.collect()  # Precaution before instantiating framebuf
ssd = SSD(spi, pcs, pdc, prst, height=320, width=480)  # 320x480 default
from gui.core.tgui import Display, quiet

# quiet()  # Comment this out for periodic free RAM messages

# Touch configuration
from touch.xpt2046 import XPT2046

spi = SoftSPI(mosi=Pin(13), miso=Pin(12), sck=Pin(15))  # 2.5MHz max
tpad = XPT2046(spi, Pin(14, Pin.OUT, value=1), ssd)
# To create a tpad.init line for your displays please read SETUP.md
tpad.init(480, 320, 139, 198, 3981, 3915, False, True, True)  # Landscape
# tpad.init(480, 320, 160, 165, 4002, 3933, True, True, False)  # Portrait
display = Display(ssd, tpad)
