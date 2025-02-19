# calendar.py Test Grid class. Requires date.py.

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2023 Peter Hinch

# touch_setup must be imported before other modules because of RAM use.
import touch_setup  # Create a display instance
from gui.core.tgui import Screen, ssd

from gui.widgets import Grid, CloseButton, Label, Button
from gui.core.writer import CWriter

# Font for CWriter
import gui.fonts.font10 as font
import gui.fonts.font14 as font1
from gui.core.colors import *
from .date import DateCal


class BaseScreen(Screen):
    def __init__(self):

        super().__init__()
        btn = {"height": 30, "callback": self.adjust, "shape": CIRCLE, "litcolor": WHITE}
        self.date = DateCal()
        wri = CWriter(ssd, font, GREEN, BLACK, False)
        wri1 = CWriter(ssd, font1, WHITE, BLACK, False)
        col = 2
        row = 2
        rows = 6
        cols = 7
        self.ncells = cols * (rows - 1)  # Row 0 has day labels
        self.last_cell = cols * rows
        colwidth = 35
        self.lbl = Label(wri, row, col, text=(colwidth + 4) * cols, justify=Label.CENTRE)
        row = self.lbl.mrow
        self.grid = Grid(wri, row, col, colwidth, rows, cols, justify=Label.CENTRE)
        self.grid[0, 0:7] = iter([d[:3] for d in DateCal.days])  # 3-char day names

        row = self.grid.mrow + 4
        ht = 30
        b = Button(wri, row, col, text="y-", args=("y", -1), **btn)
        col = b.mcol + 2
        b = Button(wri, row, col, text="y+", args=("y", 1), **btn)
        col = b.mcol + 5
        b = Button(wri, row, col, text="m-", args=("m", -1), **btn)
        col = b.mcol + 2
        b = Button(wri, row, col, text="m+", args=("m", 1), **btn)
        col = b.mcol + 5
        b = Button(wri, row, col, text="w-", args=("d", -7), **btn)
        col = b.mcol + 2
        b = Button(wri, row, col, text="w+", args=("d", 7), **btn)
        col = b.mcol + 5
        b = Button(wri, row, col, text="d-", args=("d", -1), **btn)
        col = b.mcol + 2
        b = Button(wri, row, col, text="d+", args=("d", 1), **btn)
        col = b.mcol + 5
        b = Button(wri, row, col, fgcolor=BLUE, text="H", args=("h",), **btn)
        # row = b.mrow + 10
        col = 2
        row = ssd.height - (wri1.height + 2)
        self.lblnow = Label(wri1, row, col, text=ssd.width - 4, fgcolor=WHITE)
        self.update()
        CloseButton(wri)  # Quit the application

    def adjust(self, _, f, n=0):
        d = self.date
        if f == "y":
            d.year += n
        elif f == "m":
            d.month += n
        elif f == "d":
            d.day += n
        elif f == "h":
            d.now()
        self.update()

    def days(self, month_length):  # Produce content for every cell
        for n in range(self.ncells + 1):
            yield str(n + 1) if n < month_length else ""

    def update(self):
        grid = self.grid
        cur = self.date  # Currency
        self.lbl.value(f"{DateCal.months[cur.month - 1]} {cur.year}")
        # Populate day number cells
        values = self.days(cur.month_length)  # Instantiate generator
        idx_1 = 7 + cur.wday_n(1)  # Index of 1st of month
        grid[idx_1 : self.last_cell] = values  # Populate from mday 1 to last cell
        grid[7:idx_1] = values  # Populate cells before 1st of month
        # Color cells of Sunday, today and currency. In collisions (e.g. today==Sun)
        # last color applied is effective
        grid[1:6, 6] = {"fgcolor": BLUE}  # Sunday color
        grid[idx_1 + cur.mday - 1] = {"fgcolor": YELLOW}  # Currency
        today = DateCal()
        if cur.year == today.year and cur.month == today.month:  # Today is in current month
            grid[idx_1 + today.mday - 1] = {"fgcolor": RED}
        self.lblnow.value(f"{today.day_str} {today.mday} {today.month_str} {today.year}")


def test():
    print("Calendar demo.")
    Screen.change(BaseScreen)  # A class is passed here, not an instance.


test()
