# cst820.py Capacitive touch driver

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2024 Peter Hinch

# It is minimal, providing only the required functionality for the touh GUI.
# Sources
# CTS816s:
# datasheet, Adafruit driver
# Arduino library: https://github.com/fbiego/CST816S/tree/main
# Espressif driver: https://github.com/espressif/esp-bsp/blob/master/components/lcd_touch/esp_lcd_touch_cst816s/esp_lcd_touch_cst816s.c
# CST820:
# LilyGo driver: https://github.com/Xinyuan-LilyGO/LilyGO-T-A76XX/blob/92e43a7aaee0b4ad08a3ee67d3b93818fa70b068/lib/SensorLib/src/touch/TouchClassCST816.cpp#L251
# Schematic https://github.com/jtobinart/Micropython_CYDc_ESP32-2432S024C/blob/main/resources/5-Schematic/2432S024-2-V1.0.png

# I2C clock rate 10KHz - 400KHz

from time import sleep_ms
from .touch import ABCTouch


class CST820(ABCTouch):
    def __init__(self, i2c, rst, ssd, addr=0x15):
        super().__init__(ssd, None)
        self.i2c = i2c
        self.addr = addr
        rst(0)
        sleep_ms(5)
        rst(1)
        sleep_ms(50)
        if (v := self.version()) != 0xB7:
            print(f"WARNING: unexpected touch chip version: {v:02X}")
        # i2c.writeto_mem(addr, 0xFE, b"\xff")  # prohibit automatic switching to low-power mode

    def acquire(self, buf=bytearray(6)):
        self.i2c.readfrom_mem_into(self.addr, 0x01, buf)
        self._x = ((buf[2] & 0xF) << 8) + buf[3]
        self._y = ((buf[4] & 0xF) << 8) + buf[5]
        return buf[1] == 1  # Touched if fingers==1

    def version(self):
        return self.i2c.readfrom_mem(self.addr, 0xA7, 1)[0]
