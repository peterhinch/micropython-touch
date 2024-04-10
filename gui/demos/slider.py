# slider.py Minimal micropython-touch demo showing a Slider with variable color.

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021-2024 Peter Hinch

# hardware_setup must be imported before other modules because of RAM use.
import hardware_setup
from gui.core.tgui import Screen, ssd

from gui.widgets import CloseButton, Slider
from gui.core.writer import CWriter

# Font for CWriter
import gui.fonts.freesans20 as font
from gui.core.colors import *


class BaseScreen(Screen):
    def __init__(self):

        super().__init__()
        wri = CWriter(ssd, font, GREEN, BLACK, verbose=False)
        col = 100
        row = 20
        Slider(
            wri,
            row,
            col,
            width=30,
            height=180,
            callback=self.slider_cb,
            bdcolor=RED,
            slotcolor=BLUE,
            legends=("0.0", "0.5", "1.0"),
            value=0.5,
        )
        CloseButton(wri)

    def slider_cb(self, s):
        v = s.value()
        if v < 0.2:
            s.color(BLUE)
        elif v > 0.8:
            s.color(RED)
        else:
            s.color(GREEN)


def test():
    print("Slider demo.")
    Screen.change(BaseScreen)


test()
