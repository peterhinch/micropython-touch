# Touchscreen interface

Touchscreen hardware comes in various forms requiring different drivers. The aim
is that all drivers are subclassed from an abstract base class (ABC) defined in
`touch.touch.py`. This should ensure that all drivers present a common API.
Touch drivers written for this GUI are minimal, offering only the functionality
required by the GUI. Currently two drivers are provided:
* TSC2007 [e.g. Adafruit](http://www.adafruit.com/products/5423)
* XPT2046 Used on many Chinese resistive touchscreens.

# Configuring a touchpad

The first step is to set up the display as described in the main README. Ensure
that the orientation is as required by the project. It is strongly advised to
run the [Quick hardware check](./README.md#16-quick-hardware-check).

Setup involves running `touch.setup.py`, following on-screen instructions, and
pasting the output into `hardware_setup.py`. Setup has the following objectives:
1. If a display has NxP pixels, ensuring that the larger number is associated
with the long axis of the touch panel.
2. Calibrating the touch panel to allow for the fact that the actual range of
the hardware may be smaller than its theoretical 0-4095 bits.
3. Mapping `(x,y)` touch coordinates onto `(row,col)` screen coordinates. This
must allow for landscape/portrait or upside down orientation.

A minimal `hardware_setup.py` to run the display may look like this:
```python
from machine import Pin, SoftI2C, SPI, freq
import gc
from drivers.ili93xx.ili9341 import ILI9341 as SSD

freq(250_000_000)  # RP2 overclock
# Create and export an SSD instance
prst = Pin(8, Pin.OUT, value=1)
pdc = Pin(9, Pin.OUT, value=0)  # Arbitrary pins
pcs = Pin(10, Pin.OUT, value=1)
spi = SPI(0, sck=Pin(6), mosi=Pin(7), miso=Pin(4), baudrate=30_000_000)
gc.collect()  # Precaution before instantiating framebuf
ssd = SSD(spi, pcs, pdc, prst, height=240, width=320, usd=True)

from gui.core.tgui import Display

display = Display(ssd)  # No reference to a touchpnel
```

To add touch panel data this is adapted as follows (example is for TSC2007):
```python
from gui.core.tgui import Display
from touch.tsc2007 import TSC2007

i2c = SoftI2C(scl=Pin(27), sda=Pin(26), freq=100_000)
tpad = TSC2007(i2c)
tpad.init(ssd.height, ssd.width)

display = Display(ssd, tpad)  # Now includes touch
```
Calibration is performed by issuing
```python
import touch.setup
```
The script displays a cross at the top left of the screen. Touch it firmly with
a stylus. Repeat for the following three crosses as they appear. The script will
issue a line of code like
```python
tpad.init(240, 320, 120, 314, 3923, 3878, True, True, False)
```
It is suggested that calibration be repeated a few times as touch hardware can
be inconsistent. The last four numeric args should be studied: there should be
two fairly low values followed by two similar large ones. Once a fairly
consistent response has been achieved, the line of code should be pasted into
`hardware_setup.py` in place of the existing `tpad.init` line.

After a reboot the touch interface should work. A script `touch.check` provides
optional confirmation: reported `row` and `col` coordinates should increase as
touch is moved from the top left hand corner, downwards and to the right.

# TSC2007

Constructor. This takes the following positional args:
* `i2c` An initialised I2C bus. Baudrate should be 100_000.
* `addr=0x48` I2C address of device.

# XPT2046

Constructor. This takes the following mandatory positional args:
* `spi` An initialised SPI bus. Baudrate 2.5MHz max.
* `cspin` An initialised `Pin` instance connected to the device chip select.

Optional keyword only args:
* `variance=500`
* `verbose=True`
The keyword args define post processing of the data. This is required because
touch data can be noisy: the ABC performs averaging and also computes the
variance, rejecting sample sets with excessive values. If `verbose` is set,
a message is output when rejection occurs.

These args were provided because, in testing, cheap Chinese displays exhibited
severe noise. One instance was so bad as to be unusable.

# Under the hood

The following provides details for those wishing to adapt the code or to
contribute new touch drivers.

## Coordinates

To avoid confusion, values returned by the hardware driver are referred to as `x`
and `y`, while pixel values are `row` and `col`. Typically `x` and `y` values
might have 12 bit resolution and, due to hardware tolerances, may span less than
their nominal range with minimum values > 0 and the maximum < 4095. The ABC
compensates for these limitations and performs mapping from `(x, y)` to
`(row, col)` in accordance to the display orientation (e.g. landscape/portrait,
usd, etc.).

## Touch panel API

## Constructor

Individual touch drivers accept positional args defining the interface, Followed
by optional  Current optional args
are:
*

This is invoked in `hardware_setup.py` as follows (example is for TSC2007):
```python
from touch.tsc2007 import TSC2007
i2c = SoftI2C(scl=Pin(27), sda=Pin(26), freq=100_000)  # May be hard or soft
tpad = TSC2007(i2c, 320, 240, 332, 343, 3754, 3835)  # Args provided by test script
```
This takes the following positional arguments:
1. `i2c` An initialised I2C interface. Specific to TSC2007: it is possible that
other drivers might require a different interface.
2. `height: int` Number of pixels associated with `y` coordinate.
3. `width: int` Number of pixels associated with `x` coordinate.
4. `xmin: int` Minimum value of `x`.
5. `ymin: int` Minimum value of `y`.
6. `xmax: int` Maximum  value of `x`.
7. `ymax: int` Maximum value of `y`.

It is possible that future drivers may require extra args: the intention is that
these will be keyword-only.

## Methods

### mapping

This ensures that pixel values returned by the driver correspond with the
physical layout of the display:
```python
tpad.mapping(transpose=True, row_reflect=True)
```
Args:
1. `transpose: bool=False` If set, `row` and `col` values are transposed.
2. `row_reflect: bool=False` If set the direction of increase of `row` values is
reversed.
3. `col_reflect: bool=False` If set the direction of increase of `col` values is
reversed.

This method is called in `hardware_setup.py`. Note that there is no need to use
the `mapping` method if, when running the test scripts, directions are correct.

### poll

This is periodically called by the GUI. It may be called by user code: it takes
no args and returns `True` if the screen is touched.
