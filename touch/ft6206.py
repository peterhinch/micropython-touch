# ft6206.py Capacitive touch driver

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2024 Peter Hinch

# It is minimal, providing only the required functionality for the touh GUI.
# Sources: datasheet, Adafruit driver
# https://github.com/adafruit/Adafruit_FT6206_Library/tree/master

# I2C clock rate 10KHz - 400KHz
# Can read multiple bytes (page 20)
# Section 3.1.3 Number of touch points: 1-2 is valid (as per Adafruit)

# 0 <= x <= 240
# 0 <= y <= 320

from .touch import ABCTouch


class FT6206(ABCTouch):
    def __init__(self, i2c, ssd, addr=0x38, thresh=128):
        super().__init__(ssd, None)  # No preprocessor required
        self.i2c = i2c
        self.addr = addr
        buf = bytearray(1)
        buf[0] = thresh
        self.i2c.writeto_mem(addr, 0x80, buf)  # Set touch threshold
        self.i2c.readfrom_mem_into(addr, 0xA8, buf)
        if ok := (buf[0] == 0x11):
            self.i2c.readfrom_mem_into(addr, 0xA3, buf)
            ok = buf[0] in (0x06, 0x36, 0x64)
        if not ok:
            raise OSError("Invalid FT6206 chip type.")

    def _value(self, offs, buf=bytearray(1)):
        i2c.readfrom_mem_into(addr, offs, buf)  # b0..b3 = MSB
        ev = buf[0] & 0xC0  # Event: 0 == touch, 0x40 release. Consider this ??
        v = (buf[0] & 0x0F) << 8
        i2c.readfrom_mem_into(addr, offs + 1, buf)  # LSB
        return v | buf[0]

    # If touched, populate ._x and ._y with raw data. Return True.  ** returns 0 <= y <= 320, 0 <= x <= 240
    # If not touched return False.
    def acquire(self, buf=bytearray(11)):
        addr = self.addr
        i2c = self.i2c
        i2c.readfrom_mem_into(addr, 0x02, buf)
        t = buf[0]
        if t == 1:  # One touch
            if buf[1] & 0x40:
                return False  # The only touch was a release
        if t > 2 or t == 0:  # No touch or invalid
            return False
        # We have at least one valid touch
        if (t == 2) and ((buf[7] & 0x40) == 0):  # Touch 2 was a press
            self._x = ((buf[7] & 0x0F) << 8) | buf[8]  # Save 2nd touch
            self._y = ((buf[9] & 0x0F) << 8) | buf[10]  # Don't care about touch 1
        else:  # Either t == 1 with a valid 1st touch or touch 2 was a release
            if buf[1] & 0x40:  # Both touches were releases (is this possible?)
                return False
            self._x = ((buf[1] & 0x0F) << 8) | buf[2]  # Save 1st touch
            self._y = ((buf[3] & 0x0F) << 8) | buf[4]
        return True
