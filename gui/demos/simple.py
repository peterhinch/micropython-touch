# simple.py Minimal micropython-touch demo.

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021-2024 Peter Hinch

# hardware_setup must be imported before other modules because of RAM use.
import hardware_setup  # Create a display instance
from gui.core.tgui import Screen, ssd

from gui.widgets import Label, Button, CloseButton
from gui.core.writer import CWriter

# Font for CWriter
import gui.fonts.freesans20 as font
from gui.core.colors import *


class BaseScreen(Screen):
    def __init__(self):
        def my_callback(button, arg):
            print("Button pressed", arg)

        super().__init__()
        tbl = {"litcolor": WHITE, "height": 60, "width": 80, "callback": my_callback}
        wri = CWriter(ssd, font, GREEN, BLACK)  # Verbose
        col = 2
        row = 2
        Label(wri, row, col, "Simple Demo")
        row = 150
        Button(wri, row, col, text="Yes", args=("Yes",), **tbl)
        col += 100
        Button(wri, row, col, text="No", args=("No",), **tbl)
        CloseButton(wri, 30)  # Quit the application


def test():
    print("Simple demo: button presses print to REPL.")
    Screen.change(BaseScreen)  # A class is passed here, not an instance.


test()
