# buttons.py Extension to ugui providing pushbutton classes

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021-2024 Peter Hinch

import asyncio
from gui.core.tgui import Screen, Widget, display
from gui.core.colors import *

dolittle = lambda *_: None


class Pad(Widget):
    long_press_time = 1000
    def __init__(self, writer, row, col, *, height=20, width=50, onrelease=True,
                 callback=None, args=[], lp_callback=None, lp_args=[]):
        super().__init__(writer, row, col, height, width, None, None, None, False, True)
        self.callback = (lambda *_: None) if callback is None else callback
        self.callback_args = args
        self.onrelease = onrelease
        self.lp_callback = lp_callback
        self.lp_args = lp_args
        self.lp_task = None # Long press not in progress

    def show(self):
        pass

    def _touched(self, x, y):  # Process touch
        if self.lp_callback is not None:
            self.lp_task = asyncio.create_task(self.longpress())
        if not self.onrelease:
            self.callback(self, *self.callback_args) # Callback not a bound method so pass self

    def _untouched(self):
        if self.lp_task is not None:
            self.lp_task.cancel()
            self.lp_task = None
        if self.onrelease:
            self.callback(self, *self.callback_args) # Callback not a bound method so pass self

    async def longpress(self):
        await asyncio.sleep_ms(Pad.long_press_time)
        self.lp_callback(self, *self.lp_args)
