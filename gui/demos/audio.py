# audio.py

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021-2024 Peter Hinch

# Uses nonblocking reads rather than StreamWriter because there is no non-hacky way
# to do non-allocating writes: see https://github.com/micropython/micropython/pull/7868
# Hack was
# swriter.out_buf = wav_samples_mv[:num_read]
# await swriter.drain()
# WAV files
# The proper way is to parse the WAV file as per
# https://github.com/miketeachman/micropython-i2s-examples/blob/master/examples/wavplayer.py
# Here for simplicity we assume stereo files ripped from CD's.
#

import touch_setup  # Create a display instance
from gui.core.tgui import Screen, ssd
from machine import I2S, SPI, Pin, UART
from sdcard import SDCard
import os

# Do allocations early
# 44.1KHz, 4 bytes per sample: a buffer holds 5.8ms per KiB.
# File read: 16KiB takes 40ms
BUFSIZE = 1024 * 10  # I2S internal buffer 58ms
WAVSIZE = 1024 * 16  # File read buffer 93ms
# allocate sample arrays: two-phase buffer.
buf0 = bytearray(WAVSIZE)
buf1 = bytearray(WAVSIZE)

# ======= I2S CONFIGURATION =======
# https://docs.micropython.org/en/latest/rp2/quickref.html#i2s-bus

I2S_ID = 0
config = {
    "sck": Pin(16),
    "ws": Pin(17),
    "sd": Pin(18),
    "mode": I2S.TX,
    "bits": 16,  # Sample size in bits/channel
    "format": I2S.STEREO,
    "rate": 44100,  # Sample rate in Hz
    "ibuf": BUFSIZE,  # Buffer size
}

audio_out = I2S(I2S_ID, **config)

# ======= SD CARD =======

# SD Card on SPI1 (display is on SPI0)
BAUDRATE = 20_000_000
css = Pin(13, Pin.OUT, value=1)  # SD card
spi = SPI(1, BAUDRATE, sck=Pin(14), mosi=Pin(15), miso=Pin(12))
sd = SDCard(spi, css, BAUDRATE)
vfs = os.VfsFat(sd)
os.mount(vfs, "/sd")
root = "/sd/music"  # Location of directories containing albums


# ======= GUI =======

from gui.widgets import Button, CloseButton, HorizSlider, Listbox, Label
from gui.core.writer import CWriter

# Font for CWriter
import gui.fonts.font10 as font
import gui.fonts.icon19 as ficons
from gui.core.colors import *

import os
import gc
import asyncio
import sys

# Initial check on filesystem
try:
    artists = [x[0] for x in os.ilistdir(root) if x[1] == 0x4000]
    if len(artists):
        artists.sort()
    else:
        print("No artists found in ", root)
        sys.exit(1)
except OSError:
    print(f"Expected {root} directory not found.")
    sys.exit(1)


class SelectScreen(Screen):
    songs = []
    album = ""

    def __init__(self, wri):
        super().__init__()
        self.albums = ["Albums"]
        Label(wri, 2, 100, "Album selection")
        Listbox(
            wri,
            20,
            20,
            elements=artists,
            dlines=8,
            width=100,
            bdcolor=RED,
            callback=self.sel_artist,
        )
        self.lb2 = Listbox(
            wri,
            20,
            140,
            elements=self.albums,
            dlines=8,
            width=100,
            bdcolor=RED,
            callback=self.sel_album,
        )
        self.lb2.greyed_out(True)

    def sel_artist(self, lb):  # sort
        self.artist = lb.textvalue()
        directory = "".join((root, "/", self.artist))
        albums = [x[0] for x in os.ilistdir(directory) if x[1] == 0x4000]
        albums.sort()
        try:
            while True:
                self.albums.pop()
        except IndexError:
            pass
        for a in albums:
            self.albums.append(a)
        self.lb2.greyed_out(False)
        self.lb2.update()

    def sel_album(self, lb):
        directory = "".join((root, "/", self.artist, "/", lb.textvalue()))
        songs = [x[0] for x in os.ilistdir(directory) if x[1] != 0x4000]
        songs.sort()
        SelectScreen.songs = ["".join((directory, "/", x)) for x in songs]
        SelectScreen.album = lb.textvalue()
        Screen.back()


class BaseScreen(Screen):
    def __init__(self):

        args = {
            "bdcolor": RED,
            "slotcolor": BLUE,
            "legends": ("-48dB", "-24dB", "0dB"),
            "value": 0.5,
            "height": 25,
            "width": 200,
        }
        but = {"shape": CIRCLE, "height": 35, "litcolor": WHITE}
        super().__init__()
        self.mt = asyncio.ThreadSafeFlag()
        audio_out.irq(self.audiocb)
        # Audio status
        self.playing = False  # Track is playing
        self.stop_play = False  # Command
        self.paused = False
        self.songs = []  # Paths to songs in album
        self.song_idx = 0  # Current index into .songs
        self.offset = 0  # Offset into file
        self.volume = -3

        wri = CWriter(ssd, font, GREEN, BLACK, False)
        icons = CWriter(ssd, ficons, WHITE, BLACK, False)
        # New
        Button(wri, 2, 2, height=25, text="Album", callback=self.new, args=(wri,), fgcolor=YELLOW)
        # Replay
        Button(icons, row := 200, col := 40, text="D", callback=self.replay, fgcolor=CYAN, **but)
        # Play
        Button(icons, row, col := col + 40, text="A", callback=self.play_cb, fgcolor=GREEN, **but)
        # Pause
        Button(icons, row, col := col + 40, text="C", callback=self.pause, fgcolor=YELLOW, **but)
        # Stop
        Button(icons, row, col := col + 40, text="B", callback=self.stop, fgcolor=RED, **but)
        # Skip
        Button(icons, row, col + 40, text="E", callback=self.skip, fgcolor=BLUE, **but)
        row = 40
        col = 2
        self.lbl = Label(wri, row, col, 315)
        self.lblsong = Label(wri, self.lbl.mrow + 2, col, 315)
        row = 150
        col = 40
        HorizSlider(wri, row, col, callback=self.slider_cb, **args)
        CloseButton(wri)  # Quit the application

    def audiocb(self, i2s):  # Audio buffer empty
        self.mt.set()

    def slider_cb(self, s):
        self.volume = round(8 * (s.value() - 1))

    def play_cb(self, _):
        self.play_album()

    def pause(self, _):
        self.stop_play = True
        self.paused = True
        self.show_song()

    def stop(self, _):  # Abandon album
        self.stop_play = True
        self.paused = False
        self.song_idx = 0
        self.show_song()

    def replay(self, _):
        if self.stop_play:
            self.song_idx = max(0, self.song_idx - 1)
        else:
            self.stop_play = True  # Replay from start
        self.paused = False
        self.show_song()

    def skip(self, _):
        self.stop_play = True
        self.paused = False
        self.song_idx = min(self.song_idx + 1, len(self.songs) - 1)
        self.show_song()

    def new(self, _, wri):
        self.stop_play = True
        self.paused = False
        Screen.change(SelectScreen, args=(wri,))

    def play_album(self):
        if not self.playing:
            self.reg_task(asyncio.create_task(self.album_task()))

    def after_open(self):
        self.songs = SelectScreen.songs
        self.lbl.value(SelectScreen.album)
        if self.songs:
            self.song_idx = 0  # Start on track 0
            self.show_song()

    def show_song(self):  # 13ms
        song = self.songs[self.song_idx]
        ns = song.find(SelectScreen.album)
        ne = song[ns:].find("/") + 1
        end = song[ns + ne :].find(".wav")
        self.lblsong.value(song[ns + ne : ns + ne + end])

    async def album_task(self):
        self.playing = True  # Prevent other instances
        self.stop_play = False
        # Leave paused status unchanged
        songs = self.songs[self.song_idx :]  # Start from current index
        for song in songs:
            self.show_song()
            await self.play_song(song)
            if self.stop_play:
                break  # A callback has stopped playback
            self.song_idx += 1
        else:
            self.song_idx = 0  # Played to completion.
            self.show_song()
        self.playing = False

    # Open and play a binary wav file
    async def play_song(self, song):
        mv0 = memoryview(buf0)
        mv1 = memoryview(buf1)
        cur = mv0
        phi = False
        if not self.paused:
            # advance to first byte of Data section in WAV file. This is not
            # correct for all WAV files. See link above.
            self.offset = 44
        with open(song, "rb") as wav:
            _ = wav.seek(self.offset)
            if not (num_read := wav.readinto(cur)):  # Empty file
                return
            while not self.stop_play:
                I2S.shift(buf=cur[:num_read], bits=16, shift=self.volume)
                written = 0
                while num_read - written > 0:
                    written += audio_out.write(cur[written:num_read])  # 80-150us

                cur = mv0 if phi else mv1
                phi = not phi
                # wav_samples is now empty. I2S interface is busy. Read next block.
                if not (num_read := wav.readinto(cur)):  # Blocks 40ms
                    return  # Song end
                self.offset += len(buf0)  # Save offset in case we pause play.
                # Old buffer is emptying: wait until empty
                # Blocking from start of emptyng 40ms file read + 17ms part refresh
                # 57ms. Buffer is 93ms so margin = 33ms
                await self.mt.wait()  # Wait for I2S ready.


def test():
    print("Audio demo.")
    try:
        Screen.change(BaseScreen)  # A class is passed here, not an instance.
    finally:
        audio_out.deinit()
        print("==========  CLOSE AUDIO ==========")


test()
