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
    def __init__(self, height, width, xmin, ymin, xmax, ymax):
        # Scaling and translation. Default is landscape mode
        self._width = width  # max(width, height)  # long axis is width/cols
        self._height = height  # min(width, height)  # short axis is height/rows
        self._x0 = xmin  # Returned value for row 0
        self._y0 = ymin  # Returned value for col 0
        self._xw = (width << _SCALE) // (xmax - xmin)
        self._yh = (height << _SCALE) // (ymax - ymin)
        # Mapping
        self._rr = False  # Reflection
        self._rc = False
        self._trans = False  # Transposition
        # Raw coordinates from subclass.
        self._x = 0
        self._y = 0
        # Screen referenced coordinates
        self.row = 0
        self.col = 0

    def mapping(self, row_reflect=False, col_reflect=False, transpose=False):
        self._rr = row_reflect
        self._rc = col_reflect
        self._trans = transpose

    def cal(self):
        from time import sleep_ms

        print("Running calibration - ctrl-c to stop.")
        print("Please note whether the long axis of the display is x or y.")
        xmin, xmax, ymin, ymax = 4096, 0, 4096, 0
        try:
            while True:
                if res := self.acquire():
                    print(f"x = {self._x:04d} y = {self._y:04d}", end="\r")
                    xmin = min(xmin, self._x)
                    ymin = min(ymin, self._y)
                    xmax = max(xmax, self._x)
                    ymax = max(ymax, self._y)
                    sleep_ms(200)
        except KeyboardInterrupt:
            pass
        long = max(self._height, self._width)
        short = min(self._height, self._width)
        print("If x is long axis args are:")
        print(f"Args: {short}, {long}, {xmin}, {ymin}, {xmax}, {ymax}")
        print("If y is long axis args are:")
        print(f"Args: {long}, {short}, {xmin}, {ymin}, {xmax}, {ymax}")

    # API: GUI calls poll which returns True if touched. .row, .col hold Screen
    # referenced coordinates.
    # Subclass has method .acquire: returns True if touched and populates
    # ._row and ._col with raw data, otherwise returns False
    def poll(self):
        if res := self.acquire():
            col = ((self._x - self._x0) * self._xw) >> _SCALE
            row = ((self._y - self._y0) * self._yh) >> _SCALE
            col = max(0, min(col, self._width - 1))
            row = max(0, min(row, self._height - 1))
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
