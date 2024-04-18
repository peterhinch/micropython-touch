# check.py Set up touch panel

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2024 Peter Hinch

# The touch driver returns x and y values. The first stage of setup is to determine
# whether x or y corresponds to the long axis of the display. This cannot be determined
# programmatically. The user supplies portrait/lanscape status and the code figures
# out horizontal and vertical axes.

import hardware_setup  # Create a display instance
import time
from gui.core.tgui import ssd, display, touch
from gui.core.writer import CWriter
import gui.fonts.font10 as font
from gui.core.colors import *

wri = CWriter(ssd, font, GREEN, BLACK, verbose=False)


def main():
    rw = 50  # rect width
    rh = 30  # height
    rcol = ssd.width // 2 - rw // 2
    rrow = ssd.height // 2 - rh // 2
    ssd.rect(rcol, rrow, rw, rh, GREEN)
    display.print_centred(wri, ssd.width // 2, ssd.height // 2, "Quit")
    display.print_left(wri, 2, 2, f"Touch points, check row & col.")
    display.print_left(wri, 2, 30, f"row = ", YELLOW)
    display.print_left(wri, 2, 60, f"col = ", YELLOW)
    display.print_left(wri, 2, 90, f"x = ", CYAN)
    display.print_left(wri, 2, 120, f"y = ", CYAN)
    ssd.show()
    while True:
        if touch.poll():
            tr = touch.row
            tc = touch.col
            tx = touch._x
            ty = touch._y
            display.print_left(wri, 40, 30, f"{tr:04d}", YELLOW)
            display.print_left(wri, 40, 60, f"{tc:04d}", YELLOW)
            display.print_left(wri, 40, 90, f"{tx:04d}", CYAN)
            display.print_left(wri, 40, 120, f"{ty:04d}", CYAN)
            ssd.show()
            if (rcol < tc < rcol + rw) and (rrow < tr < (rrow + rh)):
                break
        time.sleep_ms(100)
    display.clr_scr()
    ssd.show()


s = """
For each point touched, display row and column values. These represent display coordinates.
The raw x and y values from the touch panel are also displayed. These should each cover an
approximate range of 0-4095 for 12-bit touch panels.
"""
print(s)
main()
