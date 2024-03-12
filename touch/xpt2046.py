# xpt2046.py Touch driver for XPT2046

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2024 Peter Hinch

# It is minimal, providing only the required functionality for the touh GUI.
# Sources: datasheet. The following were studied for noise reduction approach,
# mainly implemented in base class:
# https://github.com/dmquirozc/XPT2046_driver_STM32/blob/main/xpt2046.c
# https://github.com/PaulStoffregen/XPT2046_Touchscreen/blob/master/XPT2046_Touchscreen.cpp
# https://github.com/robert-hh/micropython-ili9341/blob/master/xpt2046.py

# SPI clock rate 2.5MHz max

from .touch import ABCTouch, PreProcess


class XPT2046(ABCTouch):
    def __init__(self, spi, height, width, xmin=0, ymin=0, xmax=4095, ymax=4095, *, cspin):
        prep = PreProcess(self)  # Instantiate a preprocessor
        super().__init__(height, width, xmin, ymin, xmax, ymax, prep)
        self.csn = cspin
        self.spi = spi
        self.wbuf = bytearray(3)
        self.rbuf = bytearray(3)

    def _value(self, chan):
        # PD0, PD1 == 1 See table 8: always powered, penIRQ off. Start bit == 1
        self.wbuf[0] = 0x83 | (chan << 4)  # 12 bit differential mode
        self.spi.write_readinto(self.wbuf, self.rbuf)
        return (int.from_bytes(self.rbuf, "big") >> 3) & 0xFFF

    def acquire(self) -> bool:
        self.csn(0)
        if t := (self._value(3) > 100):  # Get Z1
            self._x = self._value(5)
            self._y = self._value(1)
        self.csn(1)
        if self._y > 4070 or self._x < 10:  # Discard silly values
            t = False
        return t
