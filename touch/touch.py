# touch.py ABC for touch devices.
# Subclass implements acquisition, base class scales and transforms

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2024 Peter Hinch

_SCALE = const(18)  # 12 bits ADC -> 30 bit small int. Subclasses must be limited to 12 bits.
# Class is instantiated with calibration values
# width is assumed to be the long axis with rows and columns treated accordingly.
# For a portrait mode display transpose would be set True: in this case .poll
# returns long axis measurements as the 1st (col) result
class ABCTouch:
    def __init__(self, height, width, r0, c0, rmax, cmax):
        # Scaling and translation. Default is landscape mode
        self._width = width  # max(width, height)  # long axis is width/cols
        self._height = height  # min(width, height)  # short axis is height/rows
        if height > width:
            rmax, cmax = cmax, rmax
            r0, c0 = c0, r0
        self._r0 = r0  # Returned value for row 0
        self._c0 = c0  # Returned value for col 0
        self._rh = (height << _SCALE) // (rmax - r0)
        self._ch = (width << _SCALE) // (cmax - c0)
        # Mapping
        self._rr = False  # Reflection
        self._rc = False
        self._trans = False  # Transposition
        # Raw coordinates from subclass.
        self._rrow = 0
        self._rcol = 0
        # Screen referenced coordinates
        self.row = 0
        self.col = 0

    def mapping(self, row_reflect=False, col_reflect=False, transpose=False):
        self._rr = row_reflect
        self._rc = col_reflect
        self._trans = transpose

    # API: GUI calls poll which returns True if touched. .row, .col hold Screen
    # referenced coordinates.
    # Subclass has method .acquire: returns True if touched and populates
    # ._row and ._col with raw data, otherwise returns False
    def poll(self):
        if res := self.acquire():
            row = ((self._rrow - self._r0) * self._rh) >> _SCALE
            col = ((self._rcol - self._c0) * self._ch) >> _SCALE
            if self._rr:  # Reflection
                row = self._height - row
            if self._rc:
                col = self._width - col
            if self._trans:
                self.col = row
                self.row = col
            else:
                self.col = col
                self.row = row
        return res
