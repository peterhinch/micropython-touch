# round.py Test/demo program for micropython-touch plot. Cross-patform,

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021-2024 Peter Hinch

# Create SSD instance. Must be done first because of RAM use.
import hardware_setup

from cmath import rect, pi
import math
import asyncio

from gui.core.writer import CWriter
from gui.core.tgui import Screen, ssd
from gui.widgets.graph import PolarGraph, PolarCurve
from gui.widgets import Pad, Label

# Fonts & colors
import gui.fonts.font10 as font
from gui.core.colors import *


# ***** Define some generators to populate polar curves *****
def f1(k, nmax):
    def f(theta, k):
        return rect(math.sin(k * theta), theta)  # complex

    for n in range(nmax + 1):
        yield f(2 * pi * n / nmax, k)  # complex z


def f2(k, l, nmax):
    v1 = 1 - l + 0j
    v2 = l + 0j
    rot = rect(1, 2 * pi / nmax)
    for n in range(nmax + 1):
        yield v1 + v2
        v1 *= rot
        v2 *= rot ** k


def f3(c, r, nmax):
    rot = rect(1 - r * c / nmax, c * 2 * pi / nmax)
    v = 1 + 0j
    for n in range(nmax + 1):
        yield v
        v *= rot


# Instantiate generators with args
generators = [
    [f1(3, 150), YELLOW],
    [f1(5, 150), RED],
    [f1(7, 150), CYAN],
    [f2(5, 0.3, 150), YELLOW],
    [f2(6, 0.4, 150), MAGENTA],
    [f3(6, 0.9, 150), WHITE],
]

# ***** GUI code *****

wri = CWriter(ssd, font, GREEN, BLACK, verbose=False)


class PolarScreen(Screen):
    def __init__(self, n):
        super().__init__()
        Pad(wri, 0, 0, height=239, width=239, callback=self.cb)
        self.n = n  # Current screen number
        self.g = PolarGraph(
            wri, 2, 2, height=236, bdcolor=False, fgcolor=GREEN, gridcolor=LIGHTGREEN
        )

    def cb(self, _):  # Pad touch callback
        self.n += 1  # Point to next config entry
        if self.n < len(generators):
            Screen.change(PolarScreen, mode=Screen.REPLACE, args=(self.n,))
        else:
            Screen.back()  # Quit: there is no parent Screen instance.

    def after_open(self):  # After graph has been drawn
        gen, color = generators[self.n]  # Retrieve generator and color from config
        PolarCurve(self.g, color, gen)  # populate graph.


class BaseScreen(Screen):
    def __init__(self):
        super().__init__()
        Pad(wri, 0, 0, height=239, width=239, callback=self.cb)
        col = 40
        l = Label(wri, 100, col, "Round screen demo.", fgcolor=RED)
        l = Label(wri, l.mrow + 2, col, "Touch screen to change")
        Label(wri, l.mrow + 2, col, "function plotted.")

    def cb(self, _):  # Change to screen 0
        Screen.change(PolarScreen, mode=Screen.REPLACE, args=(0,))


def test():
    print("Plot module. Touch to change function to plot.")
    Screen.change(BaseScreen)


test()
