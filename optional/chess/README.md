# The chess game demo

# Hardware

The demo is host and display agnostic, however the quantity of RAM is critical.
The minimal spec is an ESP32 with 320x240 display. The ideal spec includes a
480x320 screen: a bigger screen enables display of the current status in terms
of the identities, quantity and value of remaining pieces.

# Dependency

The `defaultdict` library module is required by the demo. Install with
```bash
$ mpremote mip install "collections-defaultdict"
```

# Chess engine and gameplay

The demo uses a port of the
[Sunfish chess engine](https://github.com/thomasahle/sunfish)
adapted for MicroPython, namely fizban99's sunfish port
[micropython-usunfish](https://github.com/fizban99/micropython-usunfish).
It may be installed with:
```bash
$ mpremote mip install github:fizban99/micropython-usunfish
```
This has been substantially optimised for MicroPython and is now the preferred
engine.

### Alternative chess engine

The demo was originally developed to support Quan Lin's Sunfish port
[micropython-sunfish](https://github.com/jacklinquan/micropython-sunfish).
Quan Lin's Sunfish port may be installed with
```bash
$ mpremote mip install github:jacklinquan/micropython-sunfish
```
### Notes

Sunfish, and thus the ports, are released under the GPL V3.0 licence.

The demo requires a display with at least 320x240 pixels. A 480x320 screen will
provide extra information such as current tallies of pieces held by each player.
The host should have plenty of RAM: development was on an ESP32-S3 with SPIRAM.
Currently there is a
[problem running on RP2350](https://github.com/fizban99/micropython-usunfish/issues/5).

Gameplay is by touching the piece to be moved, followed by a touch of the
destination square. Illegal moves are ignored. Castling is done by moving the
King: the Rook will move automatically. Pawn promotion to Queen is automatic.
_en passant_ works as expected. You get no warning if it places you in check. It
will ignore attempts to make moves which fail to deal with this, responding
properly to the first legal move.

If it checkmates you there is no indication until you attempt to make a move
when it reports the result.

The "Level" dropdown determines the maximum thinking time allowed to the target:
longer times equate to stronger play.

The easy way to run the demo is from the PC via a USB connection to the
hardware. Install the chess engine and `defaultdict`, then in a clone of this
repo, move to the `micropython-touch` directory and issue
```bash
$ mpremote mount . exec "import optional.chess.chess_game"
```

# Note for developers

The Sunfish ports have an API which is intended to be portable. If you have a
chess engine which is an improvement on Sunfish it should be straightforward to
bolt on the API, in which case `chess_game.py` would work. Similarly if you have
a preferred GUI, coding against the API would enable engines to be interchanged.

The API is documented in the [micropython-sunfish]((https://github.com/jacklinquan/micropython-sunfish))
repo.
