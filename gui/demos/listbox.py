# listbox.py micropython-touch demo of Listbox class

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021-2024 Peter Hinch

# touch_setup must be imported before other modules because of RAM use.
from touch_setup import ssd  # Create a display instance
from gui.core.tgui import Screen
from gui.core.writer import CWriter
from gui.core.colors import *

from gui.widgets import Listbox, CloseButton
import gui.fonts.freesans20 as font


class BaseScreen(Screen):
    def __init__(self):
        def cb(lb, s):
            print("Gas", s)

        def cb_radon(lb, s):  # Yeah, Radon is a gas too...
            print("Radioactive", s)

        super().__init__()
        wri = CWriter(ssd, font, GREEN, BLACK, verbose=False)
        els = (
            ("Hydrogen", cb, ("H",)),
            ("Helium", cb, ("He",)),
            ("Neon", cb, ("Ne",)),
            ("Xenon", cb, ("Xe",)),
            ("Radon", cb_radon, ("Ra",)),
            ("Uranium", cb_radon, ("U",)),
            ("Plutonium", cb_radon, ("Pu",)),
            ("Actinium", cb_radon, ("Ac",)),
        )
        Listbox(wri, 2, 2, elements=els, dlines=5, bdcolor=RED, value=1)
        # bdcolor = RED, fgcolor=RED, fontcolor = YELLOW, select_color=BLUE, value=1)
        CloseButton(wri)


Screen.change(BaseScreen)
