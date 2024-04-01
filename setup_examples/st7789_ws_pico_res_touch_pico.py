# ws_pico_res_touch.py

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2022 Peter Hinch
# With help from Tim Wermer.

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
# Note non-standard MISO pin. This works, verified by SD card.

# In shared bus devices must set baudrate to that supported by touch controller.
# This is to enable touc.setup and touch.check to work: these don't support arbitration.
spi = SPI(1, 2_500_000, sck=Pin(10), mosi=Pin(11), miso=Pin(12))

# Define the display
# For portrait mode:
# ssd = SSD(spi, height=320, width=240, dc=pdc, cs=pcs, rst=prst)
# For landscape mode:
ssd = SSD(spi, height=240, width=320, disp_mode=PORTRAIT, dc=pdc, cs=pcs, rst=prst)
from gui.core.tgui import Display

# Use of SD card is not recommended because of SPI bus sharing.
from touch.xpt2046 import XPT2046

tpad = XPT2046(spi, Pin(0), ssd)
# tpad.init(240, 320, 157, 150, 3863, 4095, True, True, False)
# Bus arbitration: pass (spi, display baud, touch baud)
display = Display(ssd, tpad, (spi, 33_000_000, 2_500_000))
