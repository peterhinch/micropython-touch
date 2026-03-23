from machine import Pin, I2C, SPI, freq
import gc
from drivers.ST7789.st7789_4bit import ST7789 as SSD

# Create and export an SSD instance
prst = Pin(39, Pin.OUT, value=1)
pdc = Pin(41, Pin.OUT, value=0)  # Arbitrary pins
pcs = Pin(42, Pin.OUT, value=1)
spi = SPI(2, sck=Pin(40), mosi=Pin(45), miso=Pin(46), baudrate=30_000_000)
gc.collect()  # Precaution before instantiating framebuf
ssd = SSD(spi, pcs, pdc, prst, height=240, width=320,disp_mode=4)
# Backlight
tft_bl = Pin(5, Pin.OUT, value=1)

# GUI configuration
from gui.core.tgui import Display

# # Touch configuration
from touch.cst328 import CST328

pint = Pin(4, Pin.IN)  # Touch interrupt
ptrst = Pin(2, Pin.OUT, value=1)  # Touch reset
i2c = I2C(0, scl=Pin(3), sda=Pin(1), freq=100_000)
tpad = CST328(i2c, ptrst, pint, ssd)
# To create a tpad.init line for your displays please read SETUP.md
# The following is consistent with the SSD constructor args above.
tpad.init(240, 320, 0, 0, 240, 320, True, False, True)
display = Display(ssd, tpad)