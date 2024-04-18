# setup.py Set up touch panel

# TODO get touch.row, touch.col for key points.
# If transpose is required, mimic transposition.
# Check for reflection.
# Use low level routines rather than GUI?


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
from gui.core.tgui import ssd, display, touch
from gui.core.writer import CWriter
import gui.fonts.font10 as font
from gui.core.colors import *


def cross(row, col, length, color):
    display.hline(col - length // 2, row, length, color)
    display.vline(col, row - length // 2, length, color)


landscape = ssd.width > ssd.height
ax = array("I", (0 for _ in range(4)))  # x
ay = array("I", (0 for _ in range(4)))  # y
wri = CWriter(ssd, font, GREEN, BLACK, verbose=False)


async def touch_state(s):
    while True:  # Wait for touch state to match passed value
        if touch.poll() == s:
            break
        # Polling at too high a rate led to bad ._x and ._y values on touch release.
        await asyncio.sleep_ms(100)


async def do_touch(n):
    ssd.show()
    await touch_state(True)  # Wait for a touch: may continue for a while
    await touch_state(False)  # Wait for release
    display.print_left(wri, 2, 50 + 30 * n, f"x = {touch._x:04d} y = {touch._y:04d}", YELLOW)
    ax[n] = touch._x
    ay[n] = touch._y
    await asyncio.sleep(1)  # Ensure touch has completed before drawing next cross


async def main():
    display.print_left(wri, 2, 2, "Touch each cross.")
    ssd.show()
    h = ssd.height
    w = ssd.width
    dh = h // 8
    dw = w // 8
    cross(dh, dw, 10, GREEN)
    await do_touch(0)

    cross(dh, w - dw, 10, GREEN)
    await do_touch(1)

    cross(h - dh, w - dw, 10, GREEN)
    await do_touch(2)

    cross(h - dh, dw, 10, GREEN)
    await do_touch(3)
    ssd.show()

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
    if x_horizontal:  # Horizontal axis is x
        xpx = l if landscape else s
        ypx = s if landscape else l
    else:  # Horizontal axis is y
        xpx = s if landscape else l
        ypx = l if landscape else s

    # print(f"Args: {xpx}, {ypx}, {xmin}, {ymin}, {xmax}, {ymax}")
    # At this stage it doesn't matter if the correct max pixel values have been assigned
    # to x and y: looking only at relative values
    # First two crosses should be on a similar row
    # Rows and cols should increase away from first cross (array index 0)
    xpose = not x_horizontal
    if xpose:  # rows are x, cols are y but touch.py reflects before transposing
        crefl = ax[0] > ax[3]
        rrefl = ay[0] > ay[1]
    else:  # rows are y, cols are x
        rrefl = ay[0] > ay[3]
        crefl = ax[0] > ax[1]

    if (not touch.precal) and (max(xmin, ymin) > 1000 or min(xmax, ymax) < 3000):
        print("WARNING: touches may not have been propoerly recorded. Please repeat setup.")
    print("Please check the following (see TOUCHPAD.md):")
    print(f"tpad.init({xpx}, {ypx}, {xmin}, {ymin}, {xmax}, {ymax}, {xpose}, {rrefl}, {crefl})")
    print("Then paste it into hardware_setup.py, replacing the initial tpad.init line.")


asyncio.run(main())
