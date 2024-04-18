# checkbox.py Minimal micropython-touch demo showing a Checkbox updating an LED.

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021-2024 Peter Hinch

# hardware_setup must be imported before other modules because of RAM use.
import hardware_setup  # Create a display instance
from gui.core.tgui import Screen, ssd

from gui.widgets import CloseButton, Checkbox, LED
from gui.core.writer import CWriter

# Font for CWriter
import gui.fonts.freesans20 as font
from gui.core.colors import *


class BaseScreen(Screen):
    def __init__(self):

        super().__init__()
        wri = CWriter(ssd, font, GREEN, BLACK, verbose=False)
        col = 50
        row = 50
        self.cb = Checkbox(wri, row, col, callback=self.cbcb)
        col += 40
        self.led = LED(wri, row, col, color=YELLOW, bdcolor=GREEN)
        CloseButton(wri)

    def cbcb(self, cb):
        self.led.value(cb.value())


def test():
    print("Checkbox demo.")
    Screen.change(BaseScreen)


test()
