# keyboard.py Test Grid class.

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2024 Peter Hinch

# hardware_setup must be imported before other modules because of RAM use.
import hardware_setup  # Create a display instance
from gui.core.tgui import Screen, ssd

from gui.widgets import Grid, CloseButton, Label, Button, Pad, Dropdown
from gui.core.writer import CWriter

# Font for CWriter
import gui.fonts.font10 as font
import gui.fonts.font14 as font1
from gui.core.colors import *


def populate(g, level):
    if level == 0:
        g[0, 0:10] = iter("1234567890")
        g[1, 0:10] = iter("qwertyuiop")
        g[2, 0:10] = iter("asdfghjkl;")
        g[3, 0:10] = iter("zxcvbnm,./")
    elif level == 1:
        g[0, 0:10] = iter("1234567890")
        g[1, 0:10] = iter("QWERTYUIOP")
        g[2, 0:10] = iter("ASDFGHJKL;")
        g[3, 0:9] = iter("ZXCVBNM,.")
        g[3, 9] = "sp"  # Special char: space
    else:
        g[0, 0:10] = iter('!"£$%^&*()')
        g[1, 0:10] = iter(";:@'#<>?/\\")
        g[2, 0:10] = iter(",.-_+=[]{}")
        g[3, 0:10] = iter("°μπωϕθαβγδ")


class BaseScreen(Screen):
    def __init__(self):

        super().__init__()
        wri = CWriter(ssd, font, GREEN, BLACK, False)
        wri1 = CWriter(ssd, font1, WHITE, BLACK, False)
        col = 2
        row = 20
        self.rows = 4  # Grid dimensions in cells
        self.cols = 10
        colwidth = 25  # Column width
        self.grid = Grid(wri, row, col, colwidth, self.rows, self.cols, justify=Label.CENTRE)
        populate(self.grid, 0)
        self.grid[0, 0] = {"bgcolor": RED}  # Initial grid currency
        self.last = (0, 0)  # Last cell touched
        ch = round((gh := self.grid.height) / self.rows)  # Height & width of a cell
        cw = round((gw := self.grid.width) / self.cols)
        self.pad = Pad(wri, row, col, height=gh, width=gw, callback=self.adjust, args=(ch, cw))
        row = self.grid.mrow + 5
        els = ("lower", "upper", "symbols")
        dd = Dropdown(wri, row, col, elements=els, callback=self.ddcb, bdcolor=YELLOW)
        b = Button(wri, row, dd.mcol + 5, text="Space", callback=self.space)
        b = Button(wri, row, b.mcol + 5, text="bsp", callback=self.bsp)
        row = dd.mrow + 5
        self.lbltxt = Label(wri1, row, col, text=ssd.width - 4, fgcolor=WHITE)
        self.lbltxt.value(">_")
        CloseButton(wri)  # Quit the application

    def adjust(self, pad, ch, cw):
        g = self.grid
        crl, ccl = self.last  # Remove highlight from previous currency
        g[crl, ccl] = {"bgcolor": BLACK}

        cr = pad.rr // ch  # Get grid coordinates of current touch
        cc = pad.rc // cw
        cl = next(g[cr, cc])  # Touched Label
        self.lbltxt.value("".join((self.lbltxt.value()[:-1], cl(), "_")))
        g[cr, cc] = {"bgcolor": RED}  # Highlight
        self.last = (cr, cc)

    def ddcb(self, dd):
        populate(self.grid, dd.value())

    def space(self, _):
        self.lbltxt.value("".join((self.lbltxt.value()[:-1], " _")))

    def bsp(self, _):
        v = self.lbltxt.value()
        if len(v) > 2:
            self.lbltxt.value("".join((v[:-2], "_")))


def test():
    print("Keyboard demo.")
    Screen.change(BaseScreen)  # A class is passed here, not an instance.


test()
