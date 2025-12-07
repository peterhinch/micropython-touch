# listbox.py Extension to ugui providing the Listbox class

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021-2024 Peter Hinch

# 13 Sep 24 Support dynamic elements list.
# 12 Sep 21 Support for scrolling.

from gui.core.tgui import Widget, display
from gui.core.colors import *
import asyncio

dolittle = lambda *_: None


class Listbox(Widget):
    NOCB = 4  # When used in a dropdown, force passed callback.

    # This is used by dropdown.py and menu.py
    @staticmethod
    def dimensions(writer, elements, dlines):
        # Height of a single entry in list.
        entry_height = writer.height + 2  # Allow a pixel above and below text
        # Number of displayable lines
        dlines = len(elements) if dlines is None else dlines
        # Height of control
        height = entry_height * dlines + 2
        simple = isinstance(elements[0], str)  # list or list of lists?
        q = (p for p in elements) if simple else (p[0] for p in elements)
        textwidth = max(writer.stringlen(x) for x in q) + 4
        return entry_height, height, dlines, textwidth

    def __init__(
        self,
        writer,
        row,
        col,
        *,
        elements,
        dlines=None,
        width=None,
        value=0,
        fgcolor=None,
        bgcolor=None,
        bdcolor=False,
        fontcolor=None,
        select_color=DARKBLUE,
        callback=dolittle,
        args=[],
        also=0
    ):

        self.els = elements
        # Check whether elements specified as (str, str,...) or ([str, callback, args], [...)
        self.simple = isinstance(self.els[0], str)
        self.cb = callback if (self.simple or also == 4) else self.despatch
        if not (self.simple or also == 4) and callback is not dolittle:
            raise ValueError("Cannot specify callback.")
        # Iterate text values
        q = (p for p in self.els) if self.simple else (p[0] for p in self.els)
        if not all(isinstance(x, str) for x in q):
            raise ValueError("Invalid elements arg.")

        # Calculate dimensions
        self.entry_height, height, self.dlines, tw = self.dimensions(writer, self.els, dlines)
        if width is None:
            width = tw  # Text width

        self.also = also  # Additioal callback events
        self.ntop = 0  # Top visible line
        if not isinstance(value, int):
            value = 0  # Or ValueError?
        elif value >= self.dlines:  # Must scroll
            value = min(value, len(elements) - 1)
            self.ntop = value - self.dlines + 1
        super().__init__(writer, row, col, height, width, fgcolor, bgcolor, bdcolor, value, True)
        self.adjustable = True  # Can show adjustable border
        self.cb_args = args
        self.select_color = select_color
        self.fontcolor = fontcolor
        self._value = value  # No callback until user selects
        self.ev = value  # Value change detection
        self.can_scroll = len(self.els) > self.dlines
        self.scroll = None  # Scroll task
        self.scrolling = False  # Scrolling in progress
        self.can_drag = True

    def despatch(self, _):  # Run the callback specified in elements
        x = self.els[self()]
        x[1](self, *x[2])

    def update(self):  # Elements list has changed.
        l = len(self.els)
        nl = self.dlines  # No. of lines that can fit in window
        self.ntop = max(0, min(self.ntop, l - nl))
        self._value = min(self._value, l - 1)
        self.show()

    def show(self):
        if not super().show(False):  # Clear to self.bgcolor
            return

        x = self.col
        y = self.row
        eh = self.entry_height
        dlines = self.dlines
        self.ntop = min(self.ntop, self._value)  # Ensure currency is visible
        self.ntop = max(self.ntop, self._value - dlines + 1)
        ntop = self.ntop
        nlines = min(dlines, len(self.els))  # Displayable lines
        for n in range(ntop, ntop + nlines):
            text = self.els[n] if self.simple else self.els[n][0]
            if self.writer.stringlen(text) > self.width:  # Clip
                font = self.writer.font
                pos = 0
                nch = 0
                for ch in text:
                    pos += font.get_ch(ch)[2]  # width of current char
                    if pos > self.width:
                        break
                    nch += 1
                text = text[:nch]
            if n == self._value:
                display.fill_rect(x, y + 1, self.width, eh - 1, self.select_color)
                display.print_left(
                    self.writer, x + 2, y + 1, text, self.fontcolor, self.select_color
                )
            else:
                display.print_left(self.writer, x + 2, y + 1, text, self.fontcolor, self.bgcolor)
            y += eh
        # Draw a vertical line to hint at scrolling
        x = self.col + self.width - 2
        if ntop:
            display.vline(x, self.row, eh - 1, self.fgcolor)
        if ntop + dlines < len(self.els):
            y = self.row + (dlines - 1) * eh
            display.vline(x, y, eh - 1, self.fgcolor)

    def textvalue(self, text=None):  # if no arg return current text
        if text is None:
            r = self.els[self._value]
            return r if self.simple else r[0]
        else:  # set value by text
            try:
                if self.simple:
                    v = self.els.index(text)
                else:  # More RAM-efficient than converting to list and using .index
                    q = (p[0] for p in self.els)
                    v = 0
                    while next(q) != text:
                        v += 1
            except (ValueError, StopIteration):
                v = None
            else:
                if v != self._value:
                    self.value(v)
            return v

    def _vchange(self, vnew):  # A value change is taking place
        # Handle scrolling
        if vnew >= self.ntop + self.dlines:
            self.ntop = vnew - self.dlines + 1
        elif vnew < self.ntop:
            self.ntop = vnew
        self._value = -1
        self.value(vnew)
        self.ev = vnew

    def do_adj(self, up):
        v = self._value
        if up:
            if v:
                self._vchange(v - 1)
        else:
            if v < len(self.els) - 1:
                self._vchange(v + 1)

    async def do_scroll(self, up):
        await asyncio.sleep(1)  # Scroll pending
        self.scrolling = True  # Scrolling in progress
        try:
            while True:
                self.do_adj(up)
                await asyncio.sleep_ms(600)
        except asyncio.CancelledError:
            self.scrolling = False

    def _touched(self, rrow, _):
        self.ev = min(rrow // self.entry_height, len(self.els) - 1) + self.ntop
        self.value(self.ev)
        if self.can_scroll and self.scroll is None:  # Scrolling is possible, not in progress.
            # If touching top or bottom element, initiate scrolling
            if rrow > self.height - self.entry_height:
                self.scroll = asyncio.create_task(self.do_scroll(False))
            elif rrow < self.entry_height:
                self.scroll = asyncio.create_task(self.do_scroll(True))

    def _untouched(self):
        if self.scroll is not None:  # Cancel actual or pending scrolling.
            self.scroll.cancel()
            self.scroll = None
        # If scrolling was in progress when touch ends, scrolling is cancelled.
        # If it was not in progress, register touch release as a value change.
        if not self.scrolling:  # Srolling was impossible, not occurring or pending.
            if self.ev is not None:
                self._value = -1  # Force update on every touch
                self.value(self.ev)
                self.cb(self, *self.cb_args)
                self.ev = None
