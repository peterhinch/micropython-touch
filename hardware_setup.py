# ili9341_pico.py Customise for your hardware config

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021-2024 Peter Hinch

# As written, supports:
# ili9341 240x320 displays on Pi Pico
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

# Bring out pins 1 and 2 for asyncio monitor.

from machine import Pin, SoftI2C, SPI, freq
import gc
import time

from drivers.ili93xx.ili9341 import ILI9341 as SSD

freq(250_000_000)  # RP2 overclock
# Create and export an SSD instance
prst = Pin(8, Pin.OUT, value=0)
pdc = Pin(9, Pin.OUT, value=0)  # Arbitrary pins
pcs = Pin(10, Pin.OUT, value=1)
spi = SPI(0, sck=Pin(6), mosi=Pin(7), miso=Pin(4), baudrate=30_000_000)
gc.collect()  # Precaution before instantiating framebuf
time.sleep_ms(100)
prst(1)
ssd = SSD(spi, pcs, pdc, prst, usd=True)  # 240x320 default
from touch.tsc2007 import TSC2007
from gui.core.tgui import Display

# SoftI2C used for PCB: hard I2C(0) does not currently work on these pins.
i2c = SoftI2C(scl=Pin(27), sda=Pin(26), freq=100_000)
# PCB has 27, 26 but MP won't accept these. Hence SoftI2C
tpad = TSC2007(i2c, 320, 240, 332, 343, 3754, 3835)
tpad.mapping(transpose=True, row_reflect=True)

display = Display(ssd, tpad)
