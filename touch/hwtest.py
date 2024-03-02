# touch.hwtest.py Hardware test of generic touchpad.

# Print constructor args for touchpanel instance.
# 1. Include observed max and min values for x and y
# 2. Ask user which is long axis and indicate order of height and width values.

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2024 Peter Hinch

import hardware_setup
from time import sleep_ms

tpad = hardware_setup.tpad
print("Running calibration - ctrl-c to stop.")
print("Please note whether the long axis of the display is x or y.")
xmin = 4096
ymin = 4096
ymax = 0
xmax = 0
try:
    while True:
        if res := tpad.acquire():
            print(f"x = {tpad._x:04d} y = {tpad._y:04d}", end="\r")
            xmin = min(xmin, tpad._x)
            ymin = min(ymin, tpad._y)
            xmax = max(xmax, tpad._x)
            ymax = max(ymax, tpad._y)
            sleep_ms(100)
except KeyboardInterrupt:
    pass
long = max(tpad._height, tpad._width)
short = min(tpad._height, tpad._width)
print("If x is long axis args are:")
print(f"Args: i2c, {short}, {long}, {xmin}, {ymin}, {xmax}, {ymax}")
print("If y is long axis args are:")
print(f"Args: i2c, {long}, {short}, {xmin}, {ymin}, {xmax}, {ymax}")
