# ili9488_ws_pico_res_touch.py

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2024-2025 Peter Hinch

# Original source https://github.com/peterhinch/micropython-touch/issues/2
# Contributor @beetlegigg.

# Supported display TFT 480x320
# https://www.waveshare.com/pico-restouch-lcd-3.5.htm

# Demo of initialisation procedure designed to minimise risk of memory fail
# when instantiating the frame buffer. The aim is to do this as early as
# possible before importing other modules.

# NOTE: This uses the ILI9486 driver because the Waveshare board has an SPI to
# parallel converter. The ILI9488 driver would be slower as the chip requires
# 18 bit/pixel color on SPI, but can use 16 bit/pixel on its parallel interface.

# WIRING for rpi pico/w

# Using waveshare LCD 3.5
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

from machine import Pin, SPI, freq
import gc
from drivers.ili94xx.ili9486 import ILI9486 as SSD

SSD.COLOR_INVERT = 0xFFFF  # Fix color inversion

# RP2 overclock
freq(250_000_000)

# Screen configuration
# (Create and export an SSD instance)
prst = Pin(15, Pin.OUT, value=1)
pdc = Pin(8, Pin.OUT, value=0)
pcs = Pin(9, Pin.OUT, value=1)

# Use hardSPI (bus 1)
spi = SPI(1, 2_500_000, sck=Pin(10), mosi=Pin(11), miso=Pin(12))
# Precaution before instantiating framebuf
gc.collect()
ssd = SSD(spi, height=320, width=480, dc=pdc, cs=pcs, rst=prst, usd=True)
from gui.core.tgui import Display, quiet

quiet()  # Comment this out for periodic free RAM messages
from touch.xpt2046 import XPT2046

# Touch configuration
tpad = XPT2046(spi, Pin(16, Pin.OUT, value=1), ssd)
# To create a tpad.init line for your displays please read SETUP.md
# tpad.init(320, 480, 202, 206, 3898, 3999, True, False, True)

# instantiate a Display
# Bus arbitration: pass (spi, display baud, touch baud)
display = Display(ssd, tpad, (spi, 33_000_000, 2_500_000))
