# setup.py Set up touch panel

# TODO get touch.row, touch.col for key points.
# If transpose is required, mimic transposition.
# Check for reflection.


# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2024 Peter Hinch

# The touch driver returns x and y values. The first stage of setup is to determine
# whether x or y corresponds to the long axis of the display. This cannot be determined
# programmatically. The user supplies portrait/lanscape status and the code figures
# out horizontal and vertical axes.

# hardware_setup must be imported before other modules because of RAM use.
import hardware_setup  # Create a display instance
import asyncio
from array import array
from gui.core.tgui import Screen, ssd, display, touch, quiet

from gui.widgets import Label
from gui.core.writer import CWriter

# Font for CWriter
import gui.fonts.font10 as font
from gui.core.colors import *
quiet()

def cross(row, col, length, color):
    display.hline(col - length // 2, row, length, color)
    display.vline(col, row - length // 2, length, color)

# User must change this (can't use screen as touch not set up)
landscape = hardware_setup.landscape

async def run():
    ax = array("I", 0 for _ in range(4))  # x
    ay = array("I", 0 for _ in range(4))  # y
    ar = array("I", 0 for _ in range(4))  # row
    ac = array("I", 0 for _ in range(4))  # col
    h = ssd.height
    w = ssd.width
    dh = h // 8
    dw = w // 8
    cross(dh, dw, 10, GREEN)
    while not touch.poll():
        await asyncio.sleep(0)
    while touch.poll():
        await asyncio.sleep(0)

    print(touch._x, touch._y)
    n = 0
    ax[n] = touch._x
    ay[n] = touch._y
    ar[n] = touch.row
    ac[n] = touch.col
    cross(dh, w - dw, 10, GREEN)
    await asyncio.sleep(1)
    while not touch.poll():
        await asyncio.sleep(0)
    while touch.poll():
        await asyncio.sleep(0)
    print(touch._x, touch._y)
    n = 1
    ax[n] = touch._x
    ay[n] = touch._y
    ar[n] = touch.row
    ac[n] = touch.col
    cross(h - dh, w - dw, 10, GREEN)
    await asyncio.sleep(1)
    while not touch.poll():
        await asyncio.sleep(0)
    while touch.poll():
        await asyncio.sleep(0)
    print(touch._x, touch._y)
    n = 2
    ax[n] = touch._x
    ay[n] = touch._y
    ar[n] = touch.row
    ac[n] = touch.col
    cross(h - dh, dw, 10, GREEN)
    await asyncio.sleep(1)
    while not touch.poll():
        await asyncio.sleep(0)
    while touch.poll():
        await asyncio.sleep(0)
    print(touch._x, touch._y)

    n = 3
    ax[n] = touch._x
    ay[n] = touch._y
    ar[n] = touch.row
    ac[n] = touch.col
    # Extrapolate to boundary: calculate margin size
    dx = (max(ax) - min(ax)) // 6
    dy = (max(ay) - min(ay)) // 6
    # Extrapolate but constrain to 12-bit range
    xmin = max(min(ax) - dx, 0)
    xmax = min(max(ax) + dx, 4095)
    ymin = max(min(ay) - dy, 0)
    ymax = min(max(ay) + dy, 4095)
    # Assign long axis pixel count to physically long axis.
    s = min(h, w)  # Short axis in pixels
    l = max(h, w)  # Long axis in pixels
    # Crosses 0 and 1 are horizontally aligned. Determine whether this is x or y.
    x_horizontal = abs(ax[0] - ax[1]) > abs(ay[0] - ay[1])
    if x_horizontal:   # Horizontal axis is x
        xpx = l if landscape else s
        ypx = s if landscape else l
    else:   # Horizontal axis is y
        xpx = s if landscape else l
        ypx = l if landscape else s

    print(f"Args: {xpx}, {ypx}, {xmin}, {ymin}, {xmax}, {ymax}")
    # At this stage it doesn't matter if the correct max pixel values have been assigned
    # to x and y: looking only at relative values
    # First two crosses should be on a similar row
    xpose = abs(ar[0] - ar[1]) > abs(ac[0] - ac[1])
    if xpose:
        ar, ac =  ac, ar
    rrefl = ar[0] > ar[3]
    crefl = ac[0] >  ac[1]
    if xpose or rrefl or crefl:
        print(f"tpad.mapping(transpose={xpose}, row_reflect={rrefl}, col_reflect={crefl})")
    else:
        print("Mapping is correct: no need to invoke tpad.mapping.")
    Screen.back()


class BaseScreen(Screen):
    def __init__(self):

        super().__init__()
        wri = CWriter(ssd, font, GREEN, BLACK, verbose=False)
        col = 2
        row = 2
        self.lbl = Label(wri, row, col, "Touch each cross.")
        self.reg_task(run())


def test():
    print("Touchpad setup: calibration.")
    Screen.change(BaseScreen)


test()
