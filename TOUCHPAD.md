# Introduction

Touch screens vary considerably in quality. Manufacturers such as Adafruit make
good quality displays: a sustained touch at a fixed location produces readings
with a high level of consistency. Further, they produce consistent results over
the entire surface with no dead zones.Chinese units can be cheap but produce
noisy outputs. Two units were tested. One was unusable: the display was fine but
one axis of touch only showed variation over about a third of its length. The
other unit could be calibrated but produced inaccurate readings close to one
edge.

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
# Touch panel code will be inserted here
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

Optional keyword-only args:
* `alen:int=10`
* `variance:int=50`
* `verbose:bool=True`
These determine the post-processing done on touch samples. When a touch occurs a
set of N samples is acquired. If the variance exceeds the `variance` value the
set is discarded and another is acquired. `alen` determines the size of the set.
If `verbose` is set a message is output each time a sample set is discarded. In
practice `variance` is determined by the quality of the touch panel. Set it too
low and all samples are discarded: the application becomes unresponsive. A value
of 50 works well with a good quality display.

Method: `init`. This has two mandatory positional args:
* `xpix` Screen dimension in pixels.
* `ypix` Screen dimension in pixels.

There are further optional args described below in "the init method". In
practice the user writes `hardware_setup.py` thus:
```python
from touch.tsc2007 import TSC2007
i2c = SoftI2C(scl=Pin(27), sda=Pin(26), freq=100_000)
tpad = TSC2007(i2c)
tpad.init(ssd.height, ssd.width)
```
The calibration script `touch.setup.py` outputs a line of code such as
```python
tpad.init(240, 320, 241, 292, 3866, 3887, True, True, False)
```
which replaces the `init` line in `hardware_setup.py`.

# XPT2046

Constructor. This takes the following mandatory positional args:
* `spi` An initialised SPI bus. Baudrate 2.5MHz max.
* `cspin` An initialised `Pin` instance connected to the device chip select.

Optional keyword-only args:
* `alen:int=10`
* `variance:int=500`
* `verbose:bool=True`
These determine the post-processing done on touch samples. When a touch occurs a
set of N samples is acquired. If the variance exceeds the `variance` value the
set is discarded and another is acquired. `alen` determines the size of the set.
If `verbose` is set a message is output each time a sample set is discarded. In
practice `variance` is determined by the quality of the touch panel. Set it too
low and all samples are discarded: the application becomes unresponsive. A value
of 50 works well with a good quality display. The default of 500 was needed for
a cheap Chinese display.

Method: `init`. This has two mandatory positional args:
* `xpix` Screen dimension in pixels.
* `ypix` Screen dimension in pixels.

There are further optional args described below in "the init method". In
practice the user writes `hardware_setup.py` thus:
```python
from touch.xpt2046 import XPT2046
spi = SoftSPI(mosi=Pin(1), miso=Pin(2), sck=Pin(3))  # 2.5MHz max
tpad = XPT2046(spi, cspin=Pin(0))
tpad.init(ssd.height, ssd.width)
```
The calibration script `touch.setup.py` outputs a line of code such as
```python
tpad.init(240, 320, 241, 292, 3866, 3887, True, True, False)
```
which replaces the `init` line in `hardware_setup.py`.

# Under the hood

The following provides details for those wishing to adapt the code or to
contribute new touch drivers.

## Design

Touchscreen hardware comes in various forms requiring different drivers. All
drivers are subclassed from `ABCTouch` defined in `touch.touch.py`. This
abstract base class performs coordinate mapping to handle calibration values,
also reflection and rotation for landcsape/portrait or USD configuration. It
also does averaging to reduce the noise present in touch measurements. This
enables hardware specific subclasses to be extremely minimal, simplifying the
development of further drivers. Currently two drivers are provided:
* TSC2007 [e.g. Adafruit](http://www.adafruit.com/products/5423)
* XPT2046 Used on many Chinese resistive touchscreens.

## Coordinates

To avoid confusion, values returned by the hardware driver are referred to as `x`
and `y`, while pixel values are `row` and `col`. Typically `x` and `y` values
might have 12 bit resolution and, due to hardware tolerances, may span less than
their nominal range with minimum values > 0 and the maximum < 4095. The ABC
compensates for these limitations and performs mapping from `(x, y)` to
`(row, col)` in accordance to the display orientation (e.g. landscape/portrait,
usd, etc.).

## API: The init method

This takes the following positional arguments:
1. `xpix: int` Number of pixels associated with `x` coordinate.
2. `ypix: int` Number of pixels associated with `y` coordinate.
3. `xmin: int=0` Minimum value of `x`.
4. `ymin: int=0` Minimum value of `y`.
5. `xmax: int=4095` Maximum  value of `x`.
6. `ymax: int=4095` Maximum value of `y`.
7. `trans:bool=False` Transpose axes.
8. `rr:bool=False` Reflect rows.
9. `rc:bool=False` Reflect columns.

Before calibration only the first two args are provided. The calibration
procedure provides the remaining args, and also corrects the order of the first
two if necessary.

### poll

This is periodically called by the GUI. It may be called by user code: it takes
no args and returns `True` if the screen is touched.
