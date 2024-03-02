# touch.swtest.py Sofware test of generic touchpad.

# Match pixel mapping to the physical orientation of the display.

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2024 Peter Hinch

import hardware_setup
from time import sleep_ms
s = """
Orient the display as it is intended to be used. Touch various points and observe the
printed row and column values. Vertical changes should affect row values, and horizontal
ones should affect the column. If the opposite is true, stop the script (ctrl-c), reset
the platform (ctrl-d), and change the transpose state. Run this script again.

Now check whether row and column values increase as you move away from the top left
corner of the screen. If this is not the case, amend the row_reflect or col_reflect values.
Again stop the script, reset the platform, and run this a final time to verify correct
behaviour.
"""
print(s)
tpad = hardware_setup.tpad
try:
    while True:
        if tpad.poll():
            print(f"row: {tpad.row:04d} col: {tpad.col:04d}\r", end="")
            sleep_ms(100)
except KeyboardInterrupt:
    pass
print()
print("Stopped.")
