# dialog.py micropython-touch demo of the DialogBox class

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021-2024 Peter Hinch

# hardware_setup must be imported before other modules because of RAM use.
import hardware_setup  # Create a display instance
from gui.core.tgui import Screen, Window, ssd

from gui.widgets import Label, Button, CloseButton, DialogBox
from gui.core.writer import CWriter

# Font for CWriter
import gui.fonts.freesans20 as font
from gui.core.colors import *


class BaseScreen(Screen):
    def __init__(self):
        super().__init__()
        # Callback for Button
        def fwd(button, my_kwargs):
            Screen.change(DialogBox, kwargs=my_kwargs)

        wri = CWriter(ssd, font, GREEN, BLACK, verbose=False)

        row = 20
        col = 20
        # Trailing spaces ensure Label is wide enough to show results
        self.lbl = Label(wri, row, col, "Dialog box test   ")
        # DialogBox constructor arguments. Here we pass all as keyword wargs.
        kwargs = {
            "writer": wri,
            "row": 20,
            "col": 20,
            "elements": (("Yes", GREEN), ("No", RED), ("Foo", YELLOW)),
            "label": "Test dialog",
        }
        row = 70
        Button(
            wri,
            row,
            col,
            text="Dialog",
            bgcolor=RED,
            textcolor=WHITE,
            callback=fwd,
            height=30,
            args=(kwargs,),
        )
        CloseButton(wri)  # Quit the application

    # Refresh the label after DialogBox has closed (but not when
    # the screen first opens).
    def after_open(self):
        if (v := Window.value()) is not None:
            self.lbl.value(f"Result: {v}")


def test():
    print("DialogBox demo.")
    Screen.change(BaseScreen)


test()
