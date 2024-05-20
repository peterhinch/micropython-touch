# round.py Test/demo program for micropython-touch plot. Cross-patform,

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021-2024 Peter Hinch

# Create SSD instance. Must be done first because of RAM use.
import hardware_setup

import cmath
import math
import asyncio

from gui.core.writer import CWriter
from gui.core.tgui import Screen, ssd
from gui.widgets.graph import PolarGraph, PolarCurve
from gui.widgets import Pad, Label

# Fonts & colors
import gui.fonts.font10 as font
from gui.core.colors import *

wri = CWriter(ssd, font, GREEN, BLACK, verbose=False)


# def fwdbutton(writer, row, col, cls_screen, text, color, *args, **kwargs):
#     def fwd(button):
#         Screen.change(cls_screen, args=args, kwargs=kwargs)
#
#     Button(
#         writer,
#         row,
#         col,
#         callback=fwd,
#         bgcolor=color,
#         text=text,
#         textcolor=BLACK,
#         height=25,
#         width=60,
#     )


class PolarScreen(Screen):
    colors = {3: YELLOW, 5: RED, 7: CYAN}

    def __init__(self, k):
        super().__init__()
        Pad(wri, 0, 0, height=239, width=239, callback=self.cb)
        self.k = k
        self.g = PolarGraph(
            wri, 2, 2, height=236, bdcolor=False, fgcolor=GREEN, gridcolor=LIGHTGREEN
        )

    def cb(self, _):
        self.k += 2
        if self.k < 9:
            Screen.change(PolarScreen, mode=Screen.REPLACE, args=(self.k,))
        else:
            Screen.back()  # Quit

    def after_open(self):  # After graph has been drawn
        def populate():
            def f(theta, k):
                return cmath.rect(math.sin(k * theta), theta)  # complex

            nmax = 150
            k = self.k
            for n in range(nmax + 1):
                yield f(2 * cmath.pi * n / nmax, k)  # complex z

        PolarCurve(self.g, PolarScreen.colors[self.k], populate())


class BaseScreen(Screen):
    def __init__(self):
        super().__init__()
        Pad(wri, 0, 0, height=239, width=239, callback=self.cb)
        col = 40
        l = Label(wri, 100, col, "Round screen demo.", fgcolor=RED)
        l = Label(wri, l.mrow + 2, col, "Touch screen to change")
        Label(wri, l.mrow + 2, col, "function plotted.")

    def cb(self, _):
        Screen.change(PolarScreen, mode=Screen.REPLACE, args=(3,))


def test():
    print("Plot module...")
    Screen.change(BaseScreen)


test()
