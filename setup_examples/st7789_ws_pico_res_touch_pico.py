# st7789_ws_pico_res_touch.py

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2022-2024 Peter Hinch
# With help from Tim Wermer.

# Supported display 240x320 with XPT2046
# https://www.waveshare.com/Pico-ResTouch-LCD-2.8.htm
# WIRING for rpi pico/w

# Using waveshare LCD 2.8
# LCD       picoW (GPIO)
# VCC       Vin
# GND       Gnd
# LCD_DC    8
# LCD_CS    9
# LCD_CLK   10
# MOSI      11
# MISO      12
# BackLight 13
# LCD_RST   15
# (Touch)
# TP_CS     16
# TP_IRQ    17 (unused)

# (GPIO used for SD card)
# 5		SDIO_CLK
# 18	SDIO_CMD
# 19	SDIO_DO
# 20	SDIO_D1
# 21	SDIO_D2
# 22	SDIO CS/D3

import gc
from machine import Pin, SPI
from drivers.st7789.st7789_4bit import *

SSD = ST7789

pdc = Pin(8, Pin.OUT, value=0)
pcs = Pin(9, Pin.OUT, value=1)
prst = Pin(15, Pin.OUT, value=1)
pbl = Pin(13, Pin.OUT, value=1)

gc.collect()  # Precaution before instantiating framebuf
# Max baudrate produced by Pico is 31_250_000. ST7789 datasheet allows <= 62.5MHz.

# In shared bus devices must set baudrate to that supported by touch controller.
# This is to enable touch.setup and touch.check to work: these don't support arbitration.
spi = SPI(1, 2_500_000, sck=Pin(10), mosi=Pin(11), miso=Pin(12))

# Define the display
# For portrait mode:
# ssd = SSD(spi, height=320, width=240, dc=pdc, cs=pcs, rst=prst)
# For landscape mode:
ssd = SSD(spi, height=240, width=320, disp_mode=PORTRAIT, dc=pdc, cs=pcs, rst=prst)
from gui.core.tgui import Display
from touch.xpt2046 import XPT2046

# Touch configuration.
tpad = XPT2046(spi, Pin(16), ssd)
tpad.init(240, 320, 157, 150, 3863, 4095, True, True, False)
# Bus arbitration: pass (spi, display baud, touch baud)
display = Display(ssd, tpad, (spi, 33_000_000, 2_500_000))
