# tbox.py Test/demo of Textbox widget for micropython-touch

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021-2024 Peter Hinch

# Usage:
# import gui.demos.tbox

# Initialise hardware and framebuf before importing modules.
import hardware_setup  # Create a display instance

from gui.core.tgui import Screen, ssd
from gui.core.writer import CWriter

import asyncio
from gui.core.colors import *
import gui.fonts.freesans20 as font
from gui.widgets import Label, Textbox, Button, CloseButton

wri = CWriter(ssd, font)  # verbose = True

btnargs = {"height": 30, "width": 80, "fgcolor": BLACK}


def fwdbutton(wri, row, col, cls_screen, text, bgc):
    def fwd(button):
        Screen.change(cls_screen)

    b = Button(wri, row, col, callback=fwd, bgcolor=bgc, text=text, **btnargs)
    return b.mrow


async def wrap(tb):
    s = """The textbox displays multiple lines of text in a field of fixed dimensions. \
Text may be clipped to the width of the control or may be word-wrapped. If the number \
of lines of text exceeds the height available, scrolling may be performed \
by calling a method.
"""
    tb.clear()
    tb.append(s, ntrim=100, line=0)
    while True:
        await asyncio.sleep(1)
        if not tb.scroll(1):
            break


async def clip(tb):
    ss = (
        "clip demo",
        "short",
        "longer line",
        "much longer line with spaces",
        "antidisestablishmentarianism",
        "line with\nline break",
        "Done",
    )
    tb.clear()
    for s in ss:
        tb.append(s, ntrim=100)  # Default line=None scrolls to show most recent
        await asyncio.sleep(1)


# Args for textboxes
# Positional
pargs = (2, 2, 180, 7)  # Row, Col, Width, nlines

# Keyword
tbargs = {
    "fgcolor": YELLOW,
    "bdcolor": RED,
    "bgcolor": BLACK,
}


class TBCScreen(Screen):
    def __init__(self):
        super().__init__()
        self.tb = Textbox(wri, *pargs, clip=True, **tbargs)
        CloseButton(wri)
        asyncio.create_task(self.main())

    async def main(self):
        await clip(self.tb)


class TBWScreen(Screen):
    def __init__(self):
        super().__init__()
        self.tb = Textbox(wri, *pargs, clip=False, **tbargs)
        CloseButton(wri)
        asyncio.create_task(self.main())

    async def main(self):
        await wrap(self.tb)


user_str = """The textbox displays multiple lines of text in a field of fixed dimensions. \
Text may be clipped to the width of the control or may be word-wrapped. If the number \
of lines of text exceeds the height available, scrolling may be performed \
by calling a method.

Please touch the screen to scroll this text.
"""


class TBUScreen(Screen):
    def __init__(self):
        super().__init__()
        tb = Textbox(wri, *pargs, clip=False, active=True, **tbargs)
        tb.append(user_str, ntrim=100)
        CloseButton(wri)


class MainScreen(Screen):
    def __init__(self):
        super().__init__()
        Label(wri, 2, 2, "Select test to run")
        col = 2
        row = 20
        row = fwdbutton(wri, row, col, TBWScreen, "Wrap", YELLOW) + 2
        row = fwdbutton(wri, row, col, TBCScreen, "Clip", BLUE) + 2
        fwdbutton(wri, row, col, TBUScreen, "Scroll", GREEN)
        CloseButton(wri)


def test():
    print("Textbox demo.")
    Screen.change(MainScreen)


test()
