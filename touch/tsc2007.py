# tsc2007.py MicroPython driver for TSC2007 resistive touch controller.

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2024 Peter Hinch

# Works with the Adafruit TSC2007 resistive touch driver.
# Adafruit product reference http://www.adafruit.com/products/5423

# Reference sources: the TSC2007 datasheet plus Adafruit driver
# https://github.com/adafruit/Adafruit_CircuitPython_TSC2007
# The following were studied for noise reduction approach, # mainly implemented
# in base class:
# https://github.com/dmquirozc/XPT2046_driver_STM32/blob/main/xpt2046.c
# https://github.com/PaulStoffregen/XPT2046_Touchscreen/blob/master/XPT2046_Touchscreen.cpp
# https://github.com/robert-hh/micropython-ili9341/blob/master/xpt2046.py
# It is minimal, providing only the required functionality for the touh GUI. See
# the Adafruit driver for a more full-featured driver.

from .touch import ABCTouch, PreProcess


class TSC2007(ABCTouch):
    def __init__(self, i2c, ssd, addr=0x48, *, alen=10):
        # Instantiate a preprocessor
        super().__init__(ssd, PreProcess(self, alen))
        self._i2c = i2c
        self._addr = addr
        i2c.writeto(addr, b"\x00")  # Low power/read temp

    def _value(self, buf=bytearray(2)):
        self._i2c.readfrom_into(self._addr, buf)
        return (buf[0] << 4) | (buf[1] >> 4)

    # If touched, populate ._x and ._y with raw data. Return True.
    # If not touched return False.
    def acquire(self):
        addr = self._addr
        self._i2c.writeto(addr, b"\xE4")  # Z
        if t := (self._value() > 100):  # Touched
            self._i2c.writeto(addr, b"\xC4")  # X
            self._x = self._value()
            self._i2c.writeto(addr, b"\xD4")  # Y
            self._y = self._value()
        self._i2c.writeto(addr, b"\x00")  # Low power/read temp
        return t
