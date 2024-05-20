# active.py micropython-touch demo of touch widgets

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021-2024 Peter Hinch

# Create SSD instance. Must be done first because of RAM use.
import hardware_setup
from gui.core.tgui import Screen, ssd
from gui.core.writer import CWriter
import gui.fonts.arial10 as arial10  # Font for CWriter
import gui.fonts.freesans20 as font
from gui.core.colors import *

# Widgets
from gui.widgets import (
    Label,
    Scale,
    ScaleLog,
    Button,
    CloseButton,
    Slider,
    HorizSlider,
    Knob,
    Checkbox,
)


class BaseScreen(Screen):
    def __init__(self):
        def tickcb(f, c):
            if f > 0.8:
                return RED
            if f < -0.8:
                return BLUE
            return c

        def tick_log_cb(f, c):
            if f > 20_000:
                return RED
            if f < 4:
                return BLUE
            return c

        super().__init__()
        wri = CWriter(ssd, arial10, GREEN, BLACK, verbose=False)
        wri_big = CWriter(ssd, font, GREEN, BLACK, verbose=False)

        col = 2
        row = 190
        Label(wri_big, row, col, "Result")
        row = 215
        self.lbl = Label(wri_big, row, col, 100, bdcolor=RED)

        self.vslider = Slider(
            wri,
            25,
            20,
            width=30,
            height=150,
            callback=self.slider_cb,
            bdcolor=RED,
            slotcolor=BLUE,
            legends=("0.0", "0.5", "1.0"),
            value=0.5,
        )
        col = 85
        row = 25
        self.hslider = HorizSlider(
            wri,
            row,
            col,
            callback=self.slider_cb,
            bdcolor=GREEN,
            slotcolor=BLUE,
            legends=("0.0", "0.5", "1.0"),
            value=0.7,
        )
        row += 30
        self.scale = Scale(
            wri,
            row,
            col,
            width=150,
            tickcb=tickcb,
            pointercolor=RED,
            fontcolor=YELLOW,
            bdcolor=CYAN,
            callback=self.cb,
            active=True,
        )
        row += 40
        self.scale_log = ScaleLog(
            wri,
            row,
            col,
            width=150,
            tickcb=tick_log_cb,
            pointercolor=RED,
            fontcolor=YELLOW,
            bdcolor=CYAN,
            callback=self.cb,
            value=10,
            active=True,
        )
        row += 40
        self.knob = Knob(wri, row, col, callback=self.cb, bgcolor=DARKGREEN, color=LIGHTRED)
        col = 180
        row = 155
        Checkbox(wri, row, col, callback=self.cbcb)
        row = 190
        Label(wri_big, row, col, "Enable/disable")
        CloseButton(wri_big)

    def cb(self, obj):
        self.lbl.value("{:5.3f}".format(obj.value()))

    def cbcb(self, cb):
        val = cb.value()
        self.vslider.greyed_out(val)
        self.hslider.greyed_out(val)
        self.scale.greyed_out(val)
        self.scale_log.greyed_out(val)
        self.knob.greyed_out(val)

    def slider_cb(self, s):
        self.cb(s)
        v = s.value()
        if v < 0.2:
            s.color(BLUE)
        elif v > 0.8:
            s.color(RED)
        else:
            s.color(GREEN)


def test():
    if ssd.height < 240 or ssd.width < 320:
        print(" This test requires a display of at least 320x240 pixels.")
    else:
        print("Testing micropython-touch...")
        Screen.change(BaseScreen)


test()
