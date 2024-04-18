# linked_sliders.py Minimal micropython-touch demo one Slider controlling two others.

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021-2024 Peter Hinch

# hardware_setup must be imported before other modules because of RAM use.
import hardware_setup  # Create a display instance
from gui.core.tgui import Screen, ssd

from gui.widgets import CloseButton, Slider
from gui.core.writer import CWriter

# Font for CWriter
import gui.fonts.freesans20 as font
from gui.core.colors import *


class BaseScreen(Screen):
    def __init__(self):
        args = {
            "bdcolor": RED,
            "slotcolor": BLUE,
            "legends": ("0", "5", "10"),
            "value": 0.5,
            "width": 30,
            "height": 180,
        }
        super().__init__()
        wri = CWriter(ssd, font, GREEN, BLACK, verbose=False)
        col = 50
        row = 20
        # Note: callback runs now, but other sliders have not yet been instantiated.
        self.s0 = Slider(wri, row, col, callback=self.slider_cb, **args)
        col = self.s0.mcol + 20
        self.s1 = Slider(wri, row, col, **args)
        col = self.s1.mcol + 20
        self.s2 = Slider(wri, row, col, **args)
        CloseButton(wri)

    def slider_cb(self, s):
        v = s.value()
        if hasattr(self, "s1"):  # If s1 & s2 have been instantiated
            self.s1.value(v)
            self.s2.value(v)


def test():
    print("Linked sliders. Leftmost one controls others.")
    Screen.change(BaseScreen)


test()
