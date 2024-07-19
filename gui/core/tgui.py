# tgui.py Micropython touch GUI library

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2024 Peter Hinch


import asyncio
import gc
from array import array
import sys

from gui.core.colors import *

if sys.implementation.version < (1, 20, 0):
    raise OSError("Firmware V1.20 or later required.")

# Globally available singleton objects
display = None  # Singleton instance
ssd = None
touch = None
_vb = True

gc.collect()
__version__ = (0, 1, 0)


async def _g():
    pass


type_coro = type(_g())


def quiet():
    global _vb
    _vb = False


# Allow Display instantiation without a touch interface for setup.
class DummyTouch:
    def __init__(self):
        self.row = 0
        self.col = 0

    def poll(self):
        return False


# Wrapper for global ssd object providing framebuf compatible methods.
# Populates globals display, touch and ssd.
class Display:
    # Populate array for clipped rect
    @staticmethod
    def crect(x, y, w, h):
        c = 4  # Clip pixels
        return array(
            "H",
            (
                x + c,
                y,
                x + w - c,
                y,
                x + w,
                y + c,
                x + w,
                y + h - c,
                x + w - c,
                y + h,
                x + c,
                y + h,
                x,
                y + h - c,
                x,
                y + c,
            ),
        )

    def __init__(self, objssd, objtouch=None, arbitrate=None):
        global display, ssd, touch
        ssd = objssd
        display = self
        touch = objtouch if objtouch is not None else DummyTouch()
        Screen.arbitrate = arbitrate  # Optional 3-tuple controls SPI baudrate
        self.height = ssd.height
        self.width = ssd.width
        self._is_grey = False  # Not greyed-out

    def print_centred(self, writer, x, y, text, fgcolor=None, bgcolor=None, invert=False):
        sl = writer.stringlen(text)
        writer.set_textpos(ssd, y - writer.height // 2, x - sl // 2)
        if self._is_grey:
            fgcolor = color_map[GREY_OUT]
        writer.setcolor(fgcolor, bgcolor)
        writer.printstring(text, invert)
        writer.setcolor()  # Restore defaults

    def print_left(self, writer, x, y, txt, fgcolor=None, bgcolor=None, invert=False):
        writer.set_textpos(ssd, y, x)
        if self._is_grey:
            fgcolor = color_map[GREY_OUT]
        writer.setcolor(fgcolor, bgcolor)
        writer.printstring(txt, invert)
        writer.setcolor()  # Restore defaults

    # Greying out has only one option given limitation of 4-bit display driver
    # It would be possible to do better with RGB565 but would need inverse transformation
    # to (r, g, b), scale and re-convert to integer.
    def _getcolor(self, color):
        # Takes in an integer color, bit size dependent on driver
        return color_map[GREY_OUT] if self._is_grey and color != color_map[BG] else color

    def usegrey(self, val):  # display.usegrey(True) sets greyed-out
        self._is_grey = val
        return self

    # Graphics primitives: despatch to device (i.e. framebuf) or
    # local function for methods not implemented by framebuf.
    # These methods support greying out color overrides.
    # Clear screen.
    def clr_scr(self):
        ssd.fill_rect(0, 0, self.width, self.height, color_map[BG])

    def rect(self, x1, y1, w, h, color):
        ssd.rect(x1, y1, w, h, self._getcolor(color))

    def fill_rect(self, x1, y1, w, h, color):
        ssd.fill_rect(x1, y1, w, h, self._getcolor(color))

    def vline(self, x, y, l, color):
        ssd.vline(x, y, l, self._getcolor(color))

    def hline(self, x, y, l, color):
        ssd.hline(x, y, l, self._getcolor(color))

    def line(self, x1, y1, x2, y2, color):
        ssd.line(x1, y1, x2, y2, self._getcolor(color))

    def circle(self, x0, y0, r, color):  # Draw circle (maybe grey)
        color = self._getcolor(color)
        ssd.ellipse(int(x0), int(y0), int(r), int(r), color)

    def fillcircle(self, x0, y0, r, color):  # Draw filled circle
        color = self._getcolor(color)
        ssd.ellipse(int(x0), int(y0), int(r), int(r), color, True)

    def clip_rect(self, x, y, w, h, color):
        ssd.poly(0, 0, self.crect(x, y, w, h), self._getcolor(color))

    def fill_clip_rect(self, x, y, w, h, color):
        ssd.poly(0, 0, self.crect(x, y, w, h), self._getcolor(color), True)


class Screen:
    do_gc = True  # Allow user to take control of GC
    current_screen = None
    is_shutdown = asyncio.Event()
    # The refresh lock prevents concurrent refresh and touch detect (may be on same bus)
    # Also allows user control
    rfsh_lock = asyncio.Lock()
    arbitrate = None  # Optional 3-tuple controls SPI baudrate
    BACK = 0
    STACK = 1
    REPLACE = 2

    @classmethod
    def show(cls, force):
        for obj in cls.current_screen.displaylist:
            if obj.visible:  # In a buttonlist only show visible button
                if force or obj.draw:
                    obj.show()

    @classmethod
    def change(cls, cls_new_screen, mode=1, *, args=[], kwargs={}):
        ins_old = cls.current_screen  # Current Screen instance
        # If initialising ensure there is an event loop before instantiating the
        # first Screen: it may create tasks in the constructor.
        if ins_old is None:
            loop = asyncio.get_event_loop()
        else:  # Leaving an existing screen
            for entry in ins_old.tasks:
                # Always cancel on back. Also on forward if requested.
                if entry[1] or not mode:
                    entry[0].cancel()
                    ins_old.tasks.remove(entry)  # remove from list
            ins_old.on_hide()  # Optional method in subclass
        if mode:  # STACK or REPLACE - instantiate new screen
            if isinstance(cls_new_screen, type):
                if isinstance(ins_old, Window):
                    raise ValueError("Windows are modal.")
                if mode == cls.REPLACE and isinstance(cls_new_screen, Window):
                    raise ValueError("Windows must be stacked.")
                ins_new = cls_new_screen(*args, **kwargs)  # New instance
            else:
                raise ValueError("Must pass Screen class or subclass (not instance)")
            # REPLACE: parent of new screen is parent of current screen
            ins_new.parent = ins_old if mode == cls.STACK else ins_old.parent
        else:  # mode is BACK
            ins_new = cls_new_screen  # An object, not a class
        cls.current_screen = ins_new
        ins_new.on_open()  # Optional subclass method
        ins_new._do_open(ins_old)  # Clear and redraw
        ins_new.after_open()  # Optional subclass method
        if ins_old is None:  # Initialising
            loop.run_until_complete(cls.monitor())  # Starts and ends uasyncio
            # asyncio is no longer running
            # Possible future displays with a shutdown method
            if hasattr(ssd, "shutdown"):
                ssd.shutdown()  # An EPD with a special shutdown method.
            else:
                ssd.fill(0)
                ssd.show()
            cls.current_screen = None  # Ensure another demo can run
            # Don't do asyncio.new_event_loop() as it prevents re-running
            # the same app.

    # Create singleton tasks, await application termination, tidy up and quit.
    @classmethod
    async def monitor(cls):
        mt = []
        mt.append(asyncio.create_task(cls.auto_refresh()))  # Refreshing
        mt.append(asyncio.create_task(cls._touchtest()))  # Touch handling
        if cls.do_gc:
            mt.append(asyncio.create_task(cls.garbage_collect()))
        if _vb:
            mt.append(asyncio.create_task(cls.show_ram()))  # Ram reports
        await cls.is_shutdown.wait()  # and wait for termination.
        cls.is_shutdown.clear()  # We're going down.
        # Task cancellation and shutdown
        for task in mt:
            task.cancel()
        for entry in cls.current_screen.tasks:
            # Screen instance will be discarded: no need to worry about .tasks
            entry[0].cancel()
        await asyncio.sleep_ms(0)  # Allow task cancellation to occur.

    # If the display driver has an async refresh method, determine the split
    # value which must be a factor of the height. In the unlikely event of
    # no factor, do_refresh confers no benefit, so use synchronous code.
    @classmethod
    async def auto_refresh(cls):
        arfsh = hasattr(ssd, "do_refresh")  # Refresh can be asynchronous.
        # If bus is shared, must pause between refreshes for touch responsiveness.
        arb = cls.arbitrate
        if pause := (0 if arb is None else 100):
            # if cls.arbitrate:  # Ensure we start at high baudrate
            arb[0].init(baudrate=arb[1])
        if arfsh:
            h = ssd.height
            split = max(y for y in (1, 2, 3, 5, 7) if not h % y)
            if split == 1:
                arfsh = False
        while True:
            Screen.show(False)  # Update stale controls. No physical refresh.
            # Now perform physical refresh. If there is no arbitration or user
            # locking, the lock will be acquired immediately
            async with cls.rfsh_lock:
                if arfsh:
                    await ssd.do_refresh(split)
                else:
                    ssd.show()  # Synchronous (blocking) refresh.
            await asyncio.sleep_ms(pause)  # Let user code respond to event

    @classmethod
    async def _touchtest(cls):  # Singleton coro tests all touchable instances
        arb = cls.arbitrate  # Bus arbitration
        if arb is not None:
            spi = arb[0]
        while True:
            await asyncio.sleep_ms(0)
            tl = cls.current_screen.lstactive  # Active (touchable) widgets
            ids = id(cls.current_screen)
            if arb is None:
                t = touch.poll()
            else:  # No need for Lock: synchronous code.
                spi.init(baudrate=arb[2])
                t = touch.poll()
                spi.init(baudrate=arb[1])
            if t:  # Display is touched.
                for obj in (a for a in tl if a.visible and not a.greyed_out()):
                    if obj._trytouch(touch.row, touch.col):
                        # Run user "on press" callback if touched
                        break  # No need to check other objects
                    if ids != id(Screen.current_screen):  # cb may have changed screen
                        break  # get new touchlist
            else:
                for obj in (a for a in tl if a.was_touched):
                    obj.was_touched = False  # Call _untouched once only
                    obj.busy = False
                    obj._untouched()  # Run "on release" callback

    @classmethod
    async def garbage_collect(cls):
        while cls.do_gc:
            await asyncio.sleep_ms(500)
            gc.collect()

    @staticmethod
    async def show_ram():
        while _vb:
            await asyncio.sleep(20)
            gc.collect()
            print(f"Free RAM {gc.mem_free() >> 10}KiB")

    @classmethod
    def back(cls):
        parent = cls.current_screen.parent
        if parent is None:  # Closing base screen. Quit.
            cls.is_shutdown.set()  # .monitor initiates shutdown.
        else:
            cls.change(parent, mode=cls.BACK)

    @classmethod
    def addobject(cls, obj):
        inst = cls.current_screen  # Get current screen instance
        if inst is None:
            raise OSError("You must create a Screen instance")
        # Populate list of active (touchable) widgets. Ignore disabled state
        # which may change at runtime.
        if obj.active:
            inst.lstactive.append(obj)
        inst.displaylist.append(obj)  # All displayable objects

    def __init__(self):
        self.lstactive = []  # Controls which respond to touch
        self.displaylist = []  # All displayable objects
        self.tasks = []  # Instance can register tasks for cancellation
        self.height = ssd.height  # Occupies entire display
        self.width = ssd.width
        self.row = 0
        self.col = 0
        Screen.current_screen = self
        self.parent = None

    def _do_open(self, old_screen):  # Window overrides
        dev = display.usegrey(False)
        # If opening a Screen from a Window just blank and redraw covered area
        if isinstance(old_screen, Window):
            x0, y0, x1, y1, w, h = old_screen._list_dims()
            dev.fill_rect(x0, y0, w, h, color_map[BG])  # Blank to screen BG
            for obj in [z for z in self.displaylist if z.overlaps(x0, y0, x1, y1)]:
                if obj.visible:
                    obj.show()
        # Normally clear the screen and redraw everything
        else:
            dev.clr_scr()  # Clear framebuf but don't update display
            Screen.show(True)  # Force full redraw

    # Methods optionally implemented in subclass
    def on_open(self):
        return

    def after_open(self):
        return

    def on_hide(self):
        return

    def locn(self, row, col):
        return self.row + row, self.col + col

    # Housekeeping methods
    def reg_task(self, task, on_change=False):  # May be passed a coro or a Task
        if isinstance(task, type_coro):
            task = asyncio.create_task(task)
        self.tasks.append((task, on_change))
        return task


# Very basic window class. Cuts a rectangular hole in a screen on which
# content may be drawn.
class Window(Screen):
    _value = None

    # Allow a Window to store an arbitrary object. Retrieval may be
    # done by caller, after the Window instance was deleted
    @classmethod
    def value(cls, val=None):
        if val is not None:
            cls._value = val
        return cls._value

    @staticmethod
    def close():  # More intuitive name for popup window
        Screen.back()

    def __init__(
        self,
        row,
        col,
        height,
        width,
        *,
        draw_border=True,
        bgcolor=None,
        fgcolor=None,
        writer=None,
    ):
        Screen.__init__(self)
        self.row = row
        self.col = col
        self.height = height
        self.width = width
        self.draw_border = draw_border
        self.fgcolor = fgcolor if fgcolor is not None else color_map[FG]
        self.bgcolor = bgcolor if bgcolor is not None else color_map[BG]

    def _do_open(self, old_screen):
        dev = display.usegrey(False)
        x, y = self.col, self.row
        dev.fill_rect(x, y, self.width, self.height, self.bgcolor)
        if self.draw_border:
            dev.rect(x, y, self.width, self.height, self.fgcolor)
        Screen.show(True)

    def _list_dims(self):
        w = self.width
        h = self.height
        x = self.col
        y = self.row
        return x, y, x + w, y + h, w, h


# Base class for all displayable objects
class Widget:
    def __init__(
        self,
        writer,
        row,
        col,
        height,
        width,
        fgcolor,
        bgcolor,
        bdcolor,
        value=None,
        active=False,
    ):
        self.active = active
        self._greyed_out = False
        Screen.addobject(self)
        self.screen = Screen.current_screen
        writer.set_clip(True, True, False)  # Disable scrolling text
        self.writer = writer
        # The following assumes that the widget is mal-positioned, not oversize.
        if row < 0:
            row = 0
            self.warning()
        elif row + height >= ssd.height:
            row = ssd.height - height - 1
            self.warning()
        if col < 0:
            col = 0
            self.warning()
        elif col + width >= ssd.width:
            col = ssd.width - width - 1
            self.warning()
        self.row = row
        self.col = col
        self.height = height
        self.width = width
        # Maximum row and col. Defaults for user metrics. May be overridden
        self.mrow = row + height + 2  # in subclass. Allow for border.
        self.mcol = col + width + 2
        self.visible = True  # Used by ButtonList class for invisible buttons
        self.draw = True  # Signals that obect must be redrawn
        self._value = value
        self.minval = 0  # FP value: self.minval <= value <= 1.0

        # Set colors. Writer colors cannot be None:
        #  bg == 0, fg == 1 are ultimate (monochrome) defaults.
        if fgcolor is None:
            fgcolor = writer.fgcolor
        if bgcolor is None:
            bgcolor = writer.bgcolor
        if bdcolor is None:
            bdcolor = fgcolor
        self.fgcolor = fgcolor
        self.bgcolor = bgcolor
        # bdcolor is False if no border is to be drawn
        self.bdcolor = bdcolor
        # Default colors allow restoration after dynamic change (Label)
        self.def_fgcolor = fgcolor
        self.def_bgcolor = bgcolor
        self.def_bdcolor = bdcolor
        # has_border is True if a border was drawn
        self.has_border = False
        self.callback = lambda *_: None  # Value change callback
        self.args = []
        # touch
        self.cb_end = lambda *_: None  # Touch release callbacks
        self.cbe_args = []
        self.was_touched = False  # Direct untouched to last touched widget
        self.busy = False  # Currently touched
        self.can_drag = False  # Accept multiple touches

    def warning(self):
        obj = self.__class__.__name__
        print(f"Warning: attempt to create {obj} outside screen dimensions.")

    def value(self, val=None):  # User method to get or set value
        if val is not None:
            if isinstance(val, float):
                val = min(max(val, self.minval), 1.0)
            if val != self._value:
                self._value = val
                self.draw = True  # Ensure a redraw on next refresh
                self.callback(self, *self.args)
        return self._value

    def __call__(self, val=None):
        return self.value(val)

    # Some widgets (e.g. Dial) have an associated Label
    def text(self, text=None, invert=False, fgcolor=None, bgcolor=None, bdcolor=None):
        if hasattr(self, "label"):
            self.label.value(text, invert, fgcolor, bgcolor, bdcolor)
        else:
            obj = self.__class__.__name__
            raise ValueError(f"Method {obj}.text does not exist.")

    # Called from subclass prior to populating framebuf with control
    def show(self, black=True):
        if self.screen != Screen.current_screen:
            # Can occur if a control's action is to change screen.
            return False  # Subclass abandons
        self.draw = False
        self.draw_border()
        # Blank controls' space
        if self.visible:
            dev = display.usegrey(self._greyed_out)
            x = self.col
            y = self.row
            dev.fill_rect(x, y, self.width, self.height, color_map[BG] if black else self.bgcolor)
        return True

    # Called by Screen.show(). Draw background and bounding box if required.
    # Border is always 2 pixels wide, outside control's bounding box
    def draw_border(self):
        if self.screen is Screen.current_screen:
            dev = display.usegrey(self._greyed_out)
            x = self.col - 2
            y = self.row - 2
            w = self.width + 4
            h = self.height + 4
            if isinstance(self.bdcolor, bool):  # No border
                if self.has_border:  # Border exists: erase it
                    dev.rect(x, y, w, h, color_map[BG])
                    self.has_border = False
            elif self.bdcolor:  # Border is required
                dev.rect(x, y, w, h, self.bdcolor)
                self.has_border = True

    def overlaps(self, xa, ya, xb, yb):  # Args must be sorted: xb > xa and yb > ya
        x0 = self.col
        y0 = self.row
        x1 = x0 + self.width
        y1 = y0 + self.height
        if (ya <= y1 and yb >= y0) and (xa <= x1 and xb >= x0):
            return True
        return False

    def _set_callbacks(self, cb, args, cb_end=None, cbe_args=None):
        self.callback = cb
        self.args = args
        if cb_end is not None:
            self.cb_end = cb_end
            self.cbe_args = cbe_args

    def greyed_out(self, val=None):
        if val is not None and self.active and self._greyed_out != val:
            self._greyed_out = val
            if self.screen is Screen.current_screen:
                display.usegrey(val)
                self.show()
        return self._greyed_out

    # Polled by Screen._touchtest if this is active, visible and not greyed out..
    # If touched in bounding box, process it otherwise do nothing.
    def _trytouch(self, row, col):
        rr = row - self.row  # Coords relative to widget origin
        rc = col - self.col
        if 0 <= rc <= self.width and 0 <= rr <= self.height:
            self.was_touched = True  # Cleared by Screen._touchtest
            if not self.busy or self.can_drag:
                self._touched(rr, rc)  # Called repeatedly for draggable objects
                self.busy = True  # otherwise once only
                return True
        return False

    def _untouched(self):  # Default if not defined in subclass
        self.cb_end(self, *self.cbe_args)
        # Callback not a bound method so pass self

    def _touched(self, rr, rc):
        print("DOH! _touched should be in subclass.")


# ***** TODO ******
# Can LinearIO still be generalised?

# A LinearIO widget uses the up and down buttons to vary a float. Such widgets
# have do_up and do_down methods which adjust the control's value in a
# time-dependent manner.
# class LinearIO(Widget):
# A LinearIO widget uses the up and down buttons to vary a float. Such widgets
# have do_up and do_down methods which adjust the control's value in a
# time-dependent manner.
class LinearIO(Widget):
    def __init__(
        self,
        writer,
        row,
        col,
        height,
        width,
        fgcolor,
        bgcolor,
        bdcolor,
        value,
        active,
        delta_v=0.02,
        horiz=None,
    ):
        self.delta_v = delta_v
        super().__init__(writer, row, col, height, width, fgcolor, bgcolor, bdcolor, value, active)
        # Subclass can force a touch orientation by passing a bool
        self.horiz = width > height if horiz is None else horiz
        self.mid = width >> 1 if self.horiz else height >> 1  # Midpoint for touch
        self.touch = asyncio.Event()
        self.task = asyncio.create_task(self.adjust())
        self.can_drag = True  # Allow reated calls to ._touched
        self.delta = 0

    def _touched(self, rrow, rcol):  # Given a touch, adjust according to position
        # 1.0 <= .delta <= 1.0
        mid = self.mid
        self.delta = (rcol - mid) / mid if self.horiz else (mid - rrow) / mid
        self.touch.set()

    # Handle long touch. Redefined by textbox.py, scale_log.py. Task runs forever
    # but spends most of the time waiting on an Event.
    async def adjust(self):
        while True:
            await self.touch.wait()
            self.touch.clear()
            # Cube law improves ability to make small changes, preserves sign.
            self.value(self.value() + self.delta_v * self.delta ** 3)
            await asyncio.sleep_ms(100)

    def _untouched(self):  # Default if not defined in subclass
        self.cb_end(self, *self.cbe_args)
        # Callback not a bound method so pass self
