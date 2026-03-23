# cst328.py Capacitive touch driver

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2026 fizban99

# It is minimal, providing only the required functionality for the touh GUI.
# Sources: datasheet, Adafruit driver
# Arduino library: https://github.com/CIRCUITSTATE/CSE_CST328/blob/main/src/CSE_CST328.cpp
# Tested on Waveshare ESP32-S3-Touch-LCD-2.8 (https://www.waveshare.com/wiki/ESP32-S3-Touch-LCD-2.8)
# 0 <= x < 320
# 0 <= y < 240


from time import sleep_ms
from machine import Pin
from .touch import ABCTouch


class CST328(ABCTouch):
    def __init__(self, i2c, rst, pint, ssd, addr=0x1A):
        super().__init__(ssd, None)
        self.i2c = i2c
        self.addr = addr
        self.pint = pint

        self.trig = True       # force first read even if no IRQ yet
        self.touched = False

        # reset
        rst(1)
        sleep_ms(10)
        rst(0)
        sleep_ms(10)
        rst(1)
        sleep_ms(100)
        pint.irq(self.isr, trigger=Pin.IRQ_RISING)

    def isr(self, _):
        self.trig = True

    def _write16(self, reg):
        self.i2c.writeto(self.addr, bytes((reg >> 8, reg & 0xFF)))

    def _read(self, reg, n):
        self.i2c.writeto(self.addr, bytes((reg >> 8, reg & 0xFF)), False)
        return self.i2c.readfrom(self.addr, n)

    def _read_u32(self, reg):
        b = self._read(reg, 4)
        return b[0] | (b[1] << 8) | (b[2] << 16) | (b[3] << 24)

    def acquire(self):
        # IRQ-driven if available, polling fallback otherwise

        if self.trig:
            self.trig = False
            data = self._read(0xD000, 27)

            # finger 1
            idx = 0
            if (data[idx] & 0x0F) == 0x06:
                self._x = (data[idx + 1] << 4) | ((data[idx + 3] >> 4) & 0x0F)
                self._y = (data[idx + 2] << 4) | (data[idx + 3] & 0x0F)
                self.touched = True
                return True


        self.touched = False
        return False