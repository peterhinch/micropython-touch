# slider_label.py Minimal micropython-touch demo showing a Slider controlling a Label.

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021-2024 Peter Hinch

# hardware_setup must be imported before other modules because of RAM use.
import hardware_setup  # Create a display instance
from gui.core.tgui import Screen, ssd

from gui.widgets import CloseButton, Slider, Label
from gui.core.writer import CWriter

# Font for CWriter
import gui.fonts.freesans20 as font
from gui.core.colors import *


class BaseScreen(Screen):
    def __init__(self):

        super().__init__()
        wri = CWriter(ssd, font, GREEN, BLACK, verbose=False)
        col = 2
        row = 2
        self.lbl = Label(wri, row, col, "0.500", bdcolor=RED, bgcolor=DARKGREEN)
        # Instantiate Label first, because Slider callback will run now.
        # See linked_sliders.py for another approach.
        row += 30
        col = 100
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
        self.lbl.value("{:5.3f}".format(v))


def test():
    print("Slider Label demo.")
    Screen.change(BaseScreen)


test()
