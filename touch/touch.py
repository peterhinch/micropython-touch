# touch.py ABC for touch devices.
# Subclass implements acquisition, base class scales and transforms

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2024 Peter Hinch
from array import array
from micropython import const

_SCALE = const(18)  # 12 bits ADC -> 30 bit small int. Subclasses must be limited to 12 bits.

# Separate preprocessor allows for other designs for future touch panels
# tpad subclass has method .acquire: returns True if touched and populates
# ._x and ._y with raw data, otherwise returns False
# .get acquires a set of samples and modifies ._x and ._y to provide mean
# values.
class PreProcess:
    def __init__(self, tpad, alen):
        self.tpad = tpad
        # Arrays for means
        self.ax = array("H", (0 for _ in range(alen)))
        self.ay = array("H", (0 for _ in range(alen)))
        self.alen = alen

    def get(self):
        tpad = self.tpad
        alen = self.alen
        x = tpad._x
        y = tpad._y
        ok = False
        if tpad.acquire():  # If touched, get and discard first (noisy) reading.
            for idx in range(alen):  # Populate arrays
                if not tpad.acquire():
                    break  # No or bad touch
                self.ax[idx] = tpad._x
                self.ay[idx] = tpad._y
            else:
                ok = True
        tpad._x = sum(self.ax) // alen if ok else x
        tpad._y = sum(self.ay) // alen if ok else y
        return ok


# Class is instantiated with a configured preprocessor.
class ABCTouch:
    def __init__(self, ssd, prep):
        self.get = self.acquire if prep is None else prep.get
        self.precal = prep is None
        self.init(ssd.height, ssd.width, 0, 0, 4095, 4095, False, False, False)

    # Assign orientation and calibration values.
    def init(self, xpix, ypix, xmin, ymin, xmax, ymax, trans, rr, rc):
        self._xpix = xpix  # No of pixels on x axis
        self._ypix = ypix  # Pixels on y axis
        if not self.precal:  # Scaling
            self._x0 = xmin  # Returned value for row 0
            self._y0 = ymin  # Returned value for col 0
            self._xl = (xpix << _SCALE) // (xmax - xmin)
            self._yl = (ypix << _SCALE) // (ymax - ymin)
        # Mapping
        self._rr = rr  # Row reflect
        self._rc = rc  # Col reflect
        self._trans = trans  # Transposition
        # Raw coordinates from subclass.
        self._x = 0
        self._y = 0
        # Screen referenced coordinates
        self.row = 0
        self.col = 0

    # API: GUI calls poll which returns True if touched. .row, .col hold Screen
    # referenced coordinates.
    # Preprocessor .get() calls touch subclass .acquire to get values
    def poll(self):
        if res := self.get():
            if self.precal:
                col = self._x  # This is not the true mapping of FT6206 but setup
                row = self._y  # will set ._trans
            else:
                xpx = ((self._x - self._x0) * self._xl) >> _SCALE  # Convert to pixels
                ypx = ((self._y - self._y0) * self._yl) >> _SCALE
                xpx = max(0, min(xpx, self._xpix - 1))
                ypx = max(0, min(ypx, self._ypix - 1))
                col = xpx
                row = ypx
            if self._rr:  # Reflection
                row = self._ypix - row
            if self._rc:
                col = self._xpix - col
            if self._trans:  # Transposition
                self.col = row
                self.row = col
            else:
                self.col = col
                self.row = row
        return res
