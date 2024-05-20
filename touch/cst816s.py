# cst816s.py Capacitive touch driver

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2024 Peter Hinch

# It is minimal, providing only the required functionality for the touh GUI.
# Sources: datasheet, Adafruit driver
# Arduino library: https://github.com/fbiego/CST816S/tree/main
# Espressif driver: https://github.com/espressif/esp-bsp/blob/master/components/lcd_touch/esp_lcd_touch_cst816s/esp_lcd_touch_cst816s.c
# According to
# https://github.com/espressif/esp-bsp/tree/master/components/lcd_touch/esp_lcd_touch_cst816s
# chip does not respond to I2C until after a touch. This is deeply weird but true.
# This means that version information in .version is null until first touched.
# It is not verified but is available for debug purposes.
# The only datasheet is almost useless with no register details.

# I2C clock rate 10KHz - 400KHz

# 0 <= x < 240
# 0 <= y < 240

from time import sleep_ms
from machine import Pin
from .touch import ABCTouch


class CST816S(ABCTouch):
    def __init__(self, i2c, rst, pint, ssd, addr=0x15):
        super().__init__(ssd, None)
        self.i2c = i2c
        self.addr = addr
        self.version = bytearray(3)
        rst(0)
        sleep_ms(5)
        rst(1)
        sleep_ms(50)
        self.trig = False
        self.doid = True  # Read ID on 1st touch
        self.touched = False
        pint.irq(self.isr, trigger=Pin.IRQ_RISING)

    def isr(self, _):
        self.trig = True

    def acquire(self, buf=bytearray(6)):
        if self.trig:
            self.trig = False
            if self.doid:  # Read version info
                self.i2c.readfrom_mem_into(self.addr, 0xA7, self.version)
                self.doid = False
            self.touched = True  # A touch is in progress.
            # Save state because polling can occur in the absence of an interrupt.
            self.i2c.readfrom_mem_into(self.addr, 0x01, buf)
            self._x = ((buf[2] & 0xF) << 8) + buf[3]
            self._y = ((buf[4] & 0xF) << 8) + buf[5]
            if buf[0] == 5 or (buf[2] & 0x40):  # Gesture == 5 or event == 1: touch released
                self.touched = False
        return self.touched

    # Debug version
    # def acquire(self, buf=bytearray(6)):
    #     if self.trig:
    #         self.trig = False
    #         self.touched = True  # A touch is in progress.
    #         # Save state because polling can occur in the absence of an interrupt.
    #         if self.doid:
    #             self.i2c.readfrom_mem_into(self.addr, 0xA7, self.version)  # Read version info
    #             self.doid = False
    #         self.i2c.readfrom_mem_into(self.addr, 0x01, buf)
    #         gesture = buf[0]
    #         points = buf[1]
    #         event = buf[2] >> 6
    #         self._x = ((buf[2] & 0xF) << 8) + buf[3]
    #         self._y = ((buf[4] & 0xF) << 8) + buf[5]
    #         print(f"x {self._x} y {self._y} points {points} event {event} gesture {gesture}")
    #         if gesture == 5 or event == 1:  # Touch released
    #             self.touched = False
    #     return self.touched
