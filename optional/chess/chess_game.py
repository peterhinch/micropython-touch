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

from gui.widgets import Grid, CloseButton, Label, Button, Pad, Dropdown
from gui.core.writer import CWriter

# Font for CWriter
import gui.fonts.font10 as font
import gui.fonts.font14 as font1
import optional.chess.chess_font as chess_font
import sunfish as sf
import asyncio

from gui.core.colors import *

PALE_GREY = create_color(12, 50, 50, 50)

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
    return BLACK if (col ^ row) & 1 else PALE_GREY


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
        dic["fgcolor"] = WHITE if (r.isupper() ^ invert) else RED
        dic["bgcolor"] = BLACK if ((n ^ (n >> 3)) & 1) else PALE_GREY
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
        wrichess = CWriter(ssd, chess_font, verbose=False)  # CWriter: chess glyphs
        wri = CWriter(ssd, font)
        col = 2
        row = 2
        rows = 8  # Grid dimensions in cells
        cols = 8
        colwidth = 30  # Column width
        self.invert = invert
        self.grid = Grid(
            wrichess, row, col, colwidth, rows, cols, fgcolor=WHITE, justify=Label.CENTRE
        )
        self.moved = (
            asyncio.ThreadSafeFlag()
        )  # Event hit bug https://github.com/micropython/micropython/issues/16569
        self.move = ""
        self.reg_task(self.play_game())

        self.lr = None  # Last cell touched
        self.lc = None
        self.ch = round((gh := self.grid.height) / rows)  # Height & width of a cell
        self.cw = round((gw := self.grid.width) / cols)
        self.pad = Pad(wrichess, row, col, height=gh, width=gw, callback=self.cb)
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
                await asyncio.sleep(0)
                board = None
                while board is None:  # Acquire valid move
                    await self.moved.wait()  # Wat for player/GUI
                    # self.moved.clear()
                    board = game.send(self.move)  # Get position after move
                self.populate(board)
                self.lr = None  # Invalidate last cell touched.
                await asyncio.sleep(1)  # Ensure refresh, allow time to view.
                board, mvengine = next(game)  # Sunfish calculates its move
                self.flash(*rc(mvengine[:2]), WHITE)
                self.flash(*rc(mvengine[2:]), WHITE)
                await asyncio.sleep_ms(700)  # Let user see forthcoming move
            except StopIteration as e:
                game_over = True
                print(f"Game over: you {'won' if (e ^ self.invert) else 'lost'}")

    def cb(self, pad):
        g = self.grid
        cr = pad.rr // self.ch  # Get grid coordinates of current touch
        cc = pad.rc // self.cw
        label = next(self.grid[cr, cc])
        label.value(bgcolor=WHITE)
        if not (cc == self.lc and cr == self.lr) and self.lr is not None:
            self.move = move_string(self.lr, self.lc, cr, cc)  # Pass move to play_game task
            print(self.move)
            self.moved.set()
        self.lr = cr  # Update last cell touched
        self.lc = cc

    def flash(self, r, c, color):
        async def do_flash(r, c, color):
            label.value(bgcolor=color)
            await asyncio.sleep_ms(500)
            label.value(bgcolor=get_bg(r, c))

        label = next(self.grid[r, c])
        asyncio.create_task(do_flash(r, c, color))


# Opening screen


def fwdbutton(wri, row, col, cls_screen, text, arg):
    def fwd(button):
        Screen.change(cls_screen, args=[arg])  # Callback

    Button(wri, row, col, callback=fwd, text=text, height=35, width=80)


class BaseScreen(Screen):
    def __init__(self):

        super().__init__()
        wri = CWriter(ssd, font1)
        Label(wri, 40, 30, "Play a game of chess!", fgcolor=YELLOW)
        fwdbutton(wri, 80, 100, GameScreen, "As white", False)
        fwdbutton(wri, 120, 100, GameScreen, "As black", True)
        CloseButton(wri)


def test():
    print("Chess demo.")
    Screen.change(BaseScreen)  # A class is passed here, not an instance.


test()
