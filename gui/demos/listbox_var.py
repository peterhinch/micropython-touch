# listbox_var.py micropython-touch demo of Listbox class with variable elements

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2024 Peter Hinch

# touch_setup must be imported before other modules because of RAM use.
from touch_setup import ssd  # Create a display instance
from gui.core.tgui import Screen
from gui.core.writer import CWriter
from gui.core.colors import *

from gui.widgets import Listbox, Button, CloseButton
import gui.fonts.freesans20 as font


def newtext():  # Create new listbox entries
    strings = ("Iron", "Copper", "Lead", "Zinc")
    n = 0
    while True:
        yield strings[n]
        n = (n + 1) % len(strings)


ntxt = newtext()  # Instantiate the generator


class BaseScreen(Screen):
    def __init__(self):

        super().__init__()
        wri = CWriter(ssd, font, GREEN, BLACK, verbose=False)
        self.els = [
            "Hydrogen",
            "Helium",
            "Neon",
            "Xenon",
            "Radon",
            "Uranium",
            "Plutonium",
            "Actinium",
        ]
        self.lb = Listbox(
            wri,
            2,
            2,
            elements=self.els,
            dlines=5,
            bdcolor=RED,
            value=1,
            callback=self.lbcb,
        )
        # Common button args
        tbl = {
            "litcolor": WHITE,
            "height": 25,
        }

        Button(wri, 2, 120, text="del", callback=self.delcb, **tbl)
        Button(wri, 32, 120, text="add", callback=self.addcb, **tbl)
        Button(wri, 62, 120, text="h2", callback=self.gocb, args=("Hydrogen",), **tbl)
        Button(wri, 92, 120, text="fe", callback=self.gocb, args=("Iron",), **tbl)
        CloseButton(wri)

    def lbcb(self, lb):  # Listbox callback
        print(lb.textvalue())

    def gocb(self, _, txt):  # Go button callback: Move currency to specified entry
        self.lb.textvalue(txt)

    def addcb(self, _):  # Add button callback
        self.els.append(next(ntxt))  # Append a new entry
        self.lb.update()

    def delcb(self, _):  # Delete button callback
        del self.els[self.lb.value()]  # Delete current entry
        self.lb.update()


Screen.change(BaseScreen)
