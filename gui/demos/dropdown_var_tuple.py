# dropdown_var_tuple.py micropython-touch demo of Dropdown widget with changeable elements

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2024 Peter Hinch

# touch_setup must be imported before other modules because of RAM use.
import touch_setup  # Create a display instance
from gui.core.tgui import Screen, Window, ssd

from gui.widgets import Label, Button, CloseButton, Dropdown
from gui.core.writer import CWriter

# Font for CWriter
import gui.fonts.font10 as font
from gui.core.colors import *


class BaseScreen(Screen):
    def __init__(self):

        super().__init__()
        wri = CWriter(ssd, font, GREEN, BLACK, verbose=False)

        # Create new dropdown entries
        tuples = (
            ("Iron", self.mcb, ("Fe",)),
            ("Copper", self.mcb, ("Cu",)),
            ("Lead", self.mcb, ("Pb",)),
            ("Zinc", self.mcb, ("Zn",)),
        )

        def newtup():
            n = 0
            while True:
                yield tuples[n]
                n = (n + 1) % len(tuples)

        self.ntup = newtup()  # Instantiate the generator

        col = 2
        row = 2
        self.els = [
            ("Hydrogen", self.cb, ("H",)),
            ("Helium", self.cb, ("He",)),
            ("Neon", self.cb, ("Ne",)),
            ("Xenon", self.cb, ("Xe",)),
            ("Radon", self.cb_radon, ("Ra",)),
            ("Uranium", self.cb_radon, ("U",)),
            ("Plutonium", self.cb_radon, ("Pu",)),
            ("Actinium", self.cb_radon, ("Ac",)),
        ]
        self.dd = Dropdown(
            wri,
            row,
            col,
            elements=self.els,
            dlines=5,  # Show 5 lines
            bdcolor=GREEN,
        )
        row += 30
        self.lbl = Label(wri, row, col, self.dd.width, bdcolor=RED)
        # Common button args
        tbl = {
            "litcolor": WHITE,
            "height": 25,
        }
        b = Button(wri, 2, 120, text="del", callback=self.delcb, **tbl)
        b = Button(wri, b.mrow + 2, 120, text="add", callback=self.addcb, **tbl)
        b = Button(wri, b.mrow + 10, 120, text="h2", callback=self.gocb, args=("Hydrogen",), **tbl)
        b = Button(wri, b.mrow + 2, 120, text="fe", callback=self.gocb, args=("Iron",), **tbl)
        CloseButton(wri)

    def gocb(self, _, txt):  # Go button callback: Move currency to specified entry
        self.dd.textvalue(txt)

    def addcb(self, _):  # Add button callback
        self.els.append(next(self.ntup))  # Append a new entry
        self.dd.update()

    def delcb(self, _):  # Delete button callback
        del self.els[self.dd.value()]  # Delete current entry
        self.dd.update()
        self.lbl.value(self.dd.textvalue())  # Cause value change callack to run

    def cb(self, dd, s):
        self.lbl.value(self.dd.textvalue())
        print("Gas", s)

    def mcb(self, dd, s):
        self.lbl.value(self.dd.textvalue())
        print("Metal", s)

    def cb_radon(self, dd, s):  # Yeah, Radon is a gas too...
        self.lbl.value(self.dd.textvalue())
        print("Radioactive", s)

    def after_open(self):
        self.lbl.value(self.dd.textvalue())


def test():
    print("Dropdown demo.")
    Screen.change(BaseScreen)


test()
