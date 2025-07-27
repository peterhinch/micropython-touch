# chess.py Test Grid class.

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2025 Peter Hinch

# https://github.com/jacklinquan/micropython-sunfish
# https://github.com/thomasahle/sunfish
# Sunfish must be installed using
# mpremote mip install github:jacklinquan/micropython-sunfish

# touch_setup must be imported before other modules because of RAM use.
import touch_setup  # Create a display instance
from gui.core.tgui import Screen, ssd

from gui.widgets import Grid, CloseButton, Label, Button, Pad, LED, Dropdown
from gui.core.writer import CWriter

# Font for CWriter
import gui.fonts.font10 as font
import gui.fonts.font14 as font1
import optional.chess.chess_font as chess_font
import sunfish as sf
import asyncio

from gui.core.colors import *

# Default color scheme
SQ_WHITE = create_color(12, 50, 50, 50)
SQ_BLACK = BLACK
PC_BLACK = RED  # fg color of black piece
GRID = WHITE

# Get Unicode chess symbol from ASCII
lut = {
    "": "",
    "K": "\u2654",
    "Q": "\u2655",
    "R": "\u2656",
    "B": "\u2657",
    "N": "\u2658",
    "P": "\u2659",
}


# Starting position when playing as Black.
iblack = b"rnbqkbnrpppp ppp            p                   PPPPPPPPRNBQKBNR"


def get_bg(row, col):  # Return checkerboard color
    return SQ_BLACK if (col ^ row) & 1 else SQ_WHITE


def rc(p):  # Convert a chess grid position (e.g. a1) to row, col
    return 8 - int(p[1]), ord(p[0]) - ord("a")


# Return state of each square in turn.
def get(board, invert):
    dic = {}
    gen = sf.get_board(board)  # Instantiate Sunfish generator
    n = 0
    while True:
        r = next(gen)  # Get chesspiece character
        dic["text"] = lut[r.upper()]
        dic["fgcolor"] = WHITE if (r.isupper() ^ invert) else PC_BLACK
        dic["bgcolor"] = SQ_BLACK if ((n ^ (n >> 3)) & 1) else SQ_WHITE
        yield dic
        n += 1


# Convert row-col to "a2a4" string
def move_string(rf, cf, rt, ct, ba=bytearray(4)):
    ba[0] = ord("a") + cf
    ba[1] = ord("1") + 7 - rf
    ba[2] = ord("a") + ct
    ba[3] = ord("1") + 7 - rt
    return ba.decode("utf8")


# Screen on which game is played
class GameScreen(Screen):
    def __init__(self, invert):  # invert: user plays as Black

        super().__init__()
        wric = CWriter(ssd, chess_font, verbose=False)  # CWriter: chess glyphs
        wri = CWriter(ssd, font, verbose=False)
        col = 2
        row = 2
        rows = 8  # Grid dimensions in cells
        cols = 8
        colwidth = 30  # Column width
        self.invert = invert
        self.grid = Grid(wric, row, col, colwidth, rows, cols, fgcolor=GRID, justify=Label.CENTRE)
        # Event hit bug https://github.com/micropython/micropython/issues/16569
        self.moved = asyncio.ThreadSafeFlag()
        self.move = ""
        self.reg_task(self.play_game())

        self.fg = PC_BLACK if invert else WHITE  # fgcolor of player's piece
        self.lr = None  # Last cell touched
        self.lc = None
        self.ch = round((gh := self.grid.height) / rows)  # Height & width of a cell
        self.cw = round((gw := self.grid.width) / cols)
        self.pad = Pad(wric, row, col, height=gh, width=gw, callback=self.cb)
        self.led = LED(wri, 100, ssd.width - 32, bdcolor=YELLOW, color=GREEN)
        self.led.value(True)
        CloseButton(wri)  # Quit the application

    # Fill grid with current board state.
    def populate(self, board):
        sq = get(board, self.invert)  # Instantiate generator
        for v in self.grid[0:]:
            v.value(**next(sq))

    async def play_game(self):
        game_over = False
        # Set up the board
        game = sf.game(iblack) if self.invert else sf.game()
        board, _ = next(game)  # Start generator, get initial position
        while not game_over:
            try:
                self.populate(board)
                await asyncio.sleep_ms(100)
                board = None
                while board is None:  # Acquire valid move
                    await self.moved.wait()  # Wat for player/GUI
                    # self.moved.clear()
                    board = game.send(self.move)  # Get position after move
                self.populate(board)
                self.led.color(RED)
                self.lr = None  # Invalidate last cell touched.
                await asyncio.sleep(1)  # Ensure refresh, allow time to view.
                board, mvengine = next(game)  # Sunfish calculates its move
                self.flash(*rc(mvengine[:2]))
                self.flash(*rc(mvengine[2:]))
                await asyncio.sleep_ms(700)  # Let user see forthcoming move
                self.led.color(GREEN)
            except StopIteration as e:
                game_over = True
                win = e.args[0] ^ self.invert
        print(f"Game over: you {'won' if win else 'lost'}")
        self.pad.greyed_out(True)
        await self.flash_led(win)

    def cb(self, pad):
        g = self.grid
        cr = pad.rr // self.ch  # Get grid coordinates of current touch
        cc = pad.rc // self.cw
        lr = self.lr
        lc = self.lc
        if lr is not None:  # Restore normal background of previous touch
            self.grid(lr, lc).value(bgcolor=get_bg(lr, lc), fgcolor=self.fg)
        self.grid(cr, cc).value(bgcolor=WHITE, fgcolor=self.fg)
        if not (cc == lc and cr == lr) and lr is not None:
            self.move = move_string(lr, lc, cr, cc)  # Pass move to play_game task
            print(self.move)
            self.moved.set()
        self.lr = cr  # Update last cell touched
        self.lc = cc

    def flash(self, r, c):  # Flash opponent's move
        async def do_flash(r, c):
            label.value(fgcolor=PC_BLACK, bgcolor=WHITE)
            await asyncio.sleep_ms(800)
            label.value(fgcolor=PC_BLACK, bgcolor=get_bg(r, c))
            await asyncio.sleep_ms(100)

        label = self.grid(r, c)
        asyncio.create_task(do_flash(r, c))

    async def flash_led(self, win):
        self.led.color = GREEN if win else RED
        v = True
        while True:
            self.led.value(v)
            await asyncio.sleep_ms(200)
            v = not v


# Opening screen


def fwdbutton(wri, row, col, cls_screen, text, arg):
    def fwd(button):
        Screen.change(cls_screen, args=[arg])  # Callback

    Button(wri, row, col, callback=fwd, text=text, height=35, width=80)


def cb(dd, n):
    global SQ_WHITE, SQ_BLACK, PC_BLACK, GRID
    GRID = WHITE if n == 0 else create_color(14, 50, 50, 50)
    PC_BLACK = RED if n == 0 else BLACK  # Black piece
    if n == 0:
        SQ_WHITE = create_color(12, 50, 50, 50)  # GREY
        SQ_BLACK = BLACK
    elif n == 1:
        SQ_WHITE = create_color(12, 230, 240, 207)  # Greenish
        SQ_BLACK = create_color(13, 113, 159, 92)
    elif n == 2:
        SQ_WHITE = create_color(12, 215, 177, 141)  # Cream
        SQ_BLACK = create_color(13, 166, 123, 97)  # Brown


els = (("Red on black", cb, (0,)), ("Black on green", cb, (1,)), ("Black on brown", cb, (2,)))


class BaseScreen(Screen):
    def __init__(self):

        super().__init__()
        wri = CWriter(ssd, font1, verbose=False)
        wri1 = CWriter(ssd, font, WHITE, BLACK, verbose=False)
        Label(wri, 20, 30, "Play a game of chess!", fgcolor=YELLOW)
        fwdbutton(wri, 60, 100, GameScreen, "As white", False)
        fwdbutton(wri, 100, 100, GameScreen, "As black", True)
        Label(wri1, 160, 30, "Colors")
        Dropdown(wri1, 160, 100, elements=els, bdcolor=YELLOW)
        CloseButton(wri)


def test():
    print("Chess demo.")
    Screen.change(BaseScreen)  # A class is passed here, not an instance.


test()
