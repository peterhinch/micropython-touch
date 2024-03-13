# check.py Set up touch panel

# TODO button is vertically offset in portrait mode diplay. Touch location is
# correct but image is displaced.

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

from gui.widgets import Label, Button
from gui.core.writer import CWriter

# Font for CWriter
import gui.fonts.font10 as font
from gui.core.colors import *

quiet()


class BaseScreen(Screen):
    def __init__(self):

        super().__init__()
        wri = CWriter(ssd, font, GREEN, BLACK, verbose=False)
        self.task = None
        col = 2
        row = 2
        self.lbl1 = Label(wri, row, col, 200)
        row = 50
        self.lbl2 = Label(wri, row, col, 200)

        # Centre position is touchable even if
        col = ssd.width // 2 - 25
        row = ssd.height // 2 - 10
        print(row, col, ssd.height, ssd.width)
        Button(wri, row, col, text="Quit", callback=self.cb)
        self.reg_task(self.run())

    def cb(self, _):
        self.back()

    async def run(self):
        while True:
            await asyncio.sleep_ms(100)
            self.lbl1.value(f"row = {Screen.trow:03d}")
            self.lbl2.value(f"col = {Screen.tcol:03d}")


def test():
    print("Touchpad setup: display row and column.")
    Screen.change(BaseScreen)


test()
