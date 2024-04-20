# ili9341_xpt2046_pico.py Customise for your hardware config

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021-2024 Peter Hinch

# As written, supports:
# ili9341 240x320 displays on Pi Pico.
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
# IO8  11   Rst
# IO9  12   DC
# Gnd  13   Gnd
# IO10 14   CS
# IO26 31   Touch SDA
# IO27 32   Touch SCL

from machine import Pin, SoftSPI, SPI, freq
import gc
from drivers.ili93xx.ili9341 import ILI9341 as SSD

freq(250_000_000)  # RP2 overclock
# Create and export an SSD instance
prst = Pin(8, Pin.OUT, value=1)
pdc = Pin(9, Pin.OUT, value=0)  # Arbitrary pins
pcs = Pin(10, Pin.OUT, value=1)
spi = SPI(0, sck=Pin(6), mosi=Pin(7), miso=Pin(4), baudrate=30_000_000)
gc.collect()  # Precaution before instantiating framebuf
ssd = SSD(spi, pcs, pdc, prst, height=240, width=320, usd=True)  # 240x320 default
from gui.core.tgui import Display, quiet

quiet()  # Comment this out for periodic free RAM messages

# Touch configuration
from touch.xpt2046 import XPT2046

spi = SoftSPI(mosi=Pin(1), miso=Pin(2), sck=Pin(3))  # 2.5MHz max
tpad = XPT2046(spi, Pin(0), ssd)
tpad.init(240, 320, 157, 150, 3863, 4095, True, True, True)
display = Display(ssd, tpad)
