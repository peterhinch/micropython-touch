# refresh_lock.py

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2024 Peter Hinch

# This demo assumes a large display whose drive supports segmented refresh.

import hardware_setup  # Create a display instance

try:
    from gui.core.tgui import Screen, ssd
except ImportError:  # Running under micro-gui
    from gui.core.ugui import Screen, ssd

from gui.widgets import Label, Button, ButtonList, CloseButton, LED
from gui.core.writer import CWriter
import gui.fonts.font10 as font
from gui.core.colors import *
import asyncio
from machine import Pin


class BaseScreen(Screen):
    def __init__(self):

        table = [
            {"fgcolor": YELLOW, "shape": RECTANGLE, "text": "Fast", "args": [True]},
            {"fgcolor": CYAN, "shape": RECTANGLE, "text": "Slow", "args": [False]},
        ]
        super().__init__()
        fixed_speed = not hasattr(ssd, "short_lock")
        if fixed_speed:
            print("Display does not support short_lock method.")
        self.task_count = 0
        wri = CWriter(ssd, font, GREEN, BLACK, verbose=False)
        col = 2
        row = 2
        lb = Label(wri, row, col, "Refresh test")
        self.led = LED(wri, row, lb.mcol + 20)
        row = 30
        txt = "Pause 5 secs"
        b = Button(wri, row, col, fgcolor=RED, shape=RECTANGLE, text=txt, callback=self.cb)
        row = 60
        bl = ButtonList(self.cbspeed)
        bl.greyed_out(fixed_speed)
        for t in table:  # Buttons overlay each other at same location
            bl.add_button(wri, row, col, **t)
        row = 90
        lb = Label(wri, row, col, "Scheduling rate:")
        self.lblrate = Label(wri, row, lb.mcol + 4, "000", bdcolor=RED, justify=Label.RIGHT)
        Label(wri, row, self.lblrate.mcol + 4, "Hz")
        self.reg_task(self.flash())  # Flash the LED
        self.reg_task(self.toggle())  # Run a task which measures its scheduling rate
        self.reg_task(self.report())
        CloseButton(wri)  # Quit

    def cb(self, _):  # Pause refresh
        asyncio.create_task(self.dopb())

    async def dopb(self):
        self.lblrate.value("0")
        async with Screen.rfsh_lock:
            await asyncio.sleep(5)

    def cbspeed(self, _, v):  # Fast-slow pushbutton callback
        ssd.short_lock(v)

    # Proof of stopped refresh: task keeps running but change not visible
    async def flash(self):
        while True:
            self.led.value(not self.led.value())
            await asyncio.sleep_ms(300)

    async def report(self):
        while True:
            await asyncio.sleep(1)
            self.lblrate.value(f"{self.task_count}")
            self.task_count = 0

    # Measure the scheduling rate of a minimal task
    async def toggle(self):
        while True:
            async with Screen.rfsh_lock:
                self.task_count += 1
                await asyncio.sleep_ms(0)


def test():
    print("Refresh test.")
    Screen.change(BaseScreen)


test()
