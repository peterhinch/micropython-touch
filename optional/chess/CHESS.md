# The chess game demo

This uses this fork of the
[Sunfish chess engine](https://github.com/jacklinquan/micropython-sunfish)
adapted for MicroPython. It may be installed with
```bash
$ mpremote mip install github:jacklinquan/micropython-sunfish
```
The chess engine is released under the GPL V3.0 licence.

The demo requires a display with at least 320x240 pixels. The host should have
plenty of RAM: a Raspberry Pico 2 works well. To run on a version 1 pico would
require the use of frozen bytecode. This option is untested.

Gameplay is by touching the piece to be moved, followed by a touch of the
destination square. Illegal moves are ignored. Castling is done by moving the
King: the Rook will move automatically. Pawn promotion to Queen is automatic.
_en passant_ works as expected.

The engine has limitations described in
[its README file](https://github.com/jacklinquan/micropython-sunfish). Notably:
* You get no warning if it places you in check. If you fail to deal with this, it
will end the game on its next move declaring itself the winner.
* It seems unaware of being in checkmate. You need actually to take its King
before it acknowledges its situation.

The easy way to run the demo is from the PC. In a clone of this repo, move to the
`micropython-touch` directory and issue
```bash
$ mpremote exec "import optional.chess.chess_game"
```

# Note for developers

The Sunfish engine has an API which is intended to be portable. If you have a
chess engine which is an improvement on Sunfish it should be straightforward to
bolt on the API, in which case `chess_game.py` would work. Similarly if you have
a preferred GUI, coding against the API would enable engines to be interchanged.

The API is documented in the Sunfish repo.
