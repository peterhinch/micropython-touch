# ILI9486 nano-gui driver for ili9486 displays
# As with all nano-gui displays, touch is not supported.

# Contributed by @brave-ulysses
# Copyright (c) Peter Hinch 2020
# Released under the MIT license see LICENSE

# This work is based on the following sources.
# https://github.com/rdagger/micropython-ili9341
# Also this forum thread with ideas from @minyiky:
# https://forum.micropython.org/viewtopic.php?f=18&t=9368

debug = False

from time import sleep_ms
import gc
import framebuf
import uasyncio as asyncio
from drivers.boolpalette import BoolPalette

@micropython.viper
def _lcopy(dest:ptr16, source:ptr8, lut:ptr16, length:int):
    # rgb565 - 16bit/pixel
    n = 0
    for x in range(length):
        c = source[x]
        dest[n] = lut[c >> 4]  # current pixel
        n += 1
        dest[n] = lut[c & 0x0f]  # next pixel
        n += 1


class ILI9486(framebuf.FrameBuffer):

    lut = bytearray(32)

    # Convert r, g, b in range 0-255 to a 16 bit colour value
    # LS byte goes into LUT offset 0, MS byte into offset 1
    # Same mapping in linebuf so LS byte is shifted out 1st
    # ILI9486 expects RGB order. 8 bit register writes require padding
    @staticmethod
    def rgb(r, g, b):
        return (r & 0xf8) | (g & 0xe0) >> 5 | (g & 0x1c) << 11 | (b & 0xf8) << 5

    # Transpose width & height for landscape mode
    def __init__(self, spi, cs, dc, rst, height=320, width=480, usd=False, init_spi=False):
        self._spi = spi
        self._cs = cs
        self._dc = dc
        self._rst = rst
        self.height = height
        self.width = width
        self._spi_init = init_spi
        pmode = framebuf.GS4_HMSB
        self.palette = BoolPalette(pmode)
        gc.collect()
        buf = bytearray(self.height * self.width // 2)
 
        self._mvb = memoryview(buf)
        super().__init__(buf, self.width, self.height, pmode)
        self._linebuf = bytearray(self.width * 2)

        # Hardware reset
        self._rst(0)
        sleep_ms(50)
        self._rst(1)
        sleep_ms(50)
        if self._spi_init:  # A callback was passed
            self._spi_init(spi)  # Bus may be shared
        self._lock = asyncio.Lock()
        # Send initialization commands

        self._wcmd(b'\x01')  # SWRESET Software reset
        sleep_ms(100)
        #self._wcd(b'\xb0', b'\x00\x00') 
        self._wcmd(b'\x11') # sleep out
        sleep_ms(20)
        self._wcd(b'\x3a', b'\x55') # interface pixel format 
        #self._wcd(b'\x0c', b'\x00\x66') # read display pixel format
        #self._wcd(b'\xc2', b'\x00\x44') # power control 3
        #self._wcd(b'\xc5', b'\x00\x00\x00\x00\x00\x00\x00\x00') # vcom control

        if self.height > self.width:
            self._wcd(b'\x36', b'\x48' if usd else b'\x88')  # MADCTL: RGB portrait mode
        else:  # Works for both USD
            self._wcd(b'\x36', b'\x28' if usd else b'\xe8')  # MADCTL: RGB landscape mode

        #self._wcd(b'\xb6', b'\x08\x82\x27')  # From 9341 - breaks it


        self._wcmd(b'\x11') # sleep out
        self._wcmd(b'\x29') # display on

    # Write data.
    def _wdata(self, data):
        self._dc(1)
        self._cs(0)
        self._spi.write( data )
        self._cs(1)

    # Write a command.
    def _wcmd(self, command):
        self._dc(0)
        self._cs(0)
        self._spi.write( command )
        self._cs(1)

    # Write a command followed by a data arg.
    def _wcd(self, command, data):
        self._dc(0)
        self._cs(0)
        self._spi.write( command )
        self._cs(1)
        self._dc(1)
        self._cs(0)
        self._spi.write( data )
        self._cs(1)

# Time (ESP32 stock freq) 196ms portrait, 185ms landscape.
# mem free on ESP32 43472 bytes (vs 110192)
    @micropython.native
    def showxxx(self):
        clut = ILI9486.lut
        wd = self.width // 2
        ht = self.height
        lb = self._linebuf
        buf = self._mvb
        if self._spi_init:  # A callback was passed
            self._spi_init(self._spi)  # Bus may be shared
        # Commands needed to start data write 
        scol=0
        scolh=(scol>>8&0x00ff)
        scoll=(scol&0x00ff)
        scold = bytes([0,scolh,0,scoll])
        ecol=480-1
        ecolh=(ecol>>8&0x00ff)
        ecoll=(ecol&0x00ff)
        ecold = bytes([0,ecolh,0,ecoll])
        srow=0
        srowh=(srow>>8&0x00ff)
        srowl=(srow&0x00ff)
        srowd = bytes([0,srowh,0,srowl])
        erow=320-1
        erowh=(erow>>8&0x00ff)
        erowl=(erow&0x00ff)
        erowd = bytes([0,erowh,0,erowl])

        print(scold + ecold, srowd + erowd)  # 65759, 65599
        self._wcd(b'\x00\x2a', scold + ecold)
        self._wcd(b'\x00\x2b', srowd + erowd)
        self._wcmd(b'\x00\x2c')  # WRITE_RAM
        self._dc(1)
        self._cs(0)
        for start in range(0, wd*ht, wd):  # For each line
            _lcopy(lb, buf[start :], clut, wd)  # Copy and map colors
            self._spi.write(lb)
        self._cs(1)

    @micropython.native
    def show(self):
        clut = ILI9486.lut
        wd = self.width // 2
        ht = self.height
        lb = self._linebuf
        buf = self._mvb

        if self._spi_init:  # A callback was passed
            self._spi_init(self._spi)  # Bus may be shared
        # Commands needed to start data write
        if self.width < ht:
            self._wcd(b'\x2a', int.to_bytes(self.width, 4, 'big'))  # SET_COLUMN works 0 .. width
            self._wcd(b'\x2b', int.to_bytes(0x1df, 4, 'big'))  # SET_PAGE ht, 0 or 65599 has no effect. This is default from manual based on MADCTL B5
        else:
            sc = 0
            ec = sc + self.width
            v = (sc << 16) + ec
            self._wcd(b'\x2a', b'\x00\x00\x00\x00\x00\x01\x00\xdf')
            #self._wcd(b'\x2a', int.to_bytes(65759, 8, 'big'))  # SET_COLUMN revolting hack works
            #self._wcd(b'\x2a', int.to_bytes(0x100ff, 8, 'big'))  # 100ea - 100ff
            #self._wcd(b'\x2a', int.to_bytes(self.height -1, 4, 'big'))
            #self._wcd(b'\x2b', int.to_bytes(self.width -1, 4, 'big'))  # SET_PAGE ht, 0 or 65599 has no effect

        #self._wcd(b'\x2b', int.to_bytes(65599, 8, 'big'))  # SET_PAGE
        #self._wcd(b'\x2b', int.to_bytes(ht, 4, 'big'))  # SET_PAGE
        self._wcmd(b'\x2c')  # WRITE_RAM
        self._dc(1)
        self._cs(0)
        for start in range(0, wd*ht, wd):  # For each line
            _lcopy(lb, buf[start :], clut, wd)  # Copy and map colors
            self._spi.write(lb)
        self._cs(1)

    async def do_refresh(self, split=4):
        async with self._lock:
            lines, mod = divmod(self.height, split)  # Lines per segment
            if mod:
                raise ValueError('Invalid do_refresh arg.')
            clut = ILI9486.lut
            wd = self.width // 2
            ht = self.height
            lb = self._linebuf
            buf = self._mvb
            # Commands needed to start data write 
            scol=0
            scolh=(scol>>8&0x00ff)
            scoll=(scol&0x00ff)
            scold = bytes([0,scolh,0,scoll])
            ecol=480-1
            ecolh=(ecol>>8&0x00ff)
            ecoll=(ecol&0x00ff)
            ecold = bytes([0,ecolh,0,ecoll])
            srow=0
            srowh=(srow>>8&0x00ff)
            srowl=(srow&0x00ff)
            srowd = bytes([0,srowh,0,srowl])
            erow=320-1
            erowh=(erow>>8&0x00ff)
            erowl=(erow&0x00ff)
            erowd = bytes([0,erowh,0,erowl])


            self._wcd(b'\x00\x2a', scold + ecold)
            self._wcd(b'\x00\x2b', srowd + erowd)


            self._wcmd(b'\x00\x2c')  # WRITE_RAM
            self._dc(1)
            line = 0
            for _ in range(split):  # For each segment
                if self._spi_init:  # A callback was passed
                    self._spi_init(self._spi)  # Bus may be shared
                self._cs(0)
                for start in range(wd * line, wd * (line + lines), wd):  # For each line
                    _lcopy(lb, buf[start :], clut, wd)  # Copy and map colors
                    self._spi.write(lb)
                line += lines
                self._cs(1)  # Allow other tasks to use bus
                await asyncio.sleep_ms(0)
