# Introduction

This doc serves two purposes:
1. Documenting specific touch drivers.
2. Providing an explanation of the touch calibration process and general design
information.

For setup instructions please see [setup](./SETUP.md).

Touch screens vary considerably in quality. Manufacturers such as Adafruit make
good quality displays: a sustained touch at a fixed location produces readings
with a high level of consistency. Further, they produce consistent results over
the entire surface with no dead zones.Chinese units can be cheap but produce
noisy outputs. Two units were tested. One was unusable: the display was fine but
one axis of touch only showed variation over about a third of its length. The
other unit could be calibrated but produced inaccurate readings close to one
edge.

[This Adafruit screen](https://www.adafruit.com/product/1743) was
used in development with [this touch controller](http://www.adafruit.com/products/5423)
with good results.

# Calibration

To understand calibration, note the coordinate naming convention. Values
returned by the hardware driver are referred to as `x` and `y`, while pixel
values are `row` and `col`. The `xy` values have nominal 12-bit resolution but
owing to hardware tolerances typically have a range less than the nominal. The
range of `row/col` values is precisely that of the display size in pixels.

Calibration has the following objectives:
1. If a display has NxP pixels, ensuring that the larger number is associated
with the long axis of the touch panel.
2. Calibrating the touch panel to allow for the fact that the actual range of
the hardware may be smaller than its theoretical 0-4095 bits. Thus if one axis
returns values in the range 189-3800, after calibration these will be mapped to
0-4095.
3. Mapping `(x,y)` touch coordinates onto `(row,col)` screen coordinates. This
must allow for landscape/portrait or upside down orientation. For example, if a
display has 240x320 pixels and is mounted in portrait mode, a touch near the top
left corner will issue something close to `row=0, col=0`. A touch near the
bottom right will issue something close to `row=319, col=239`.

The output of the calibration process is a line of code defining values for the
touchpad driver's `init` method. This is documented below.

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

## Mapping

The `x` and `y` values have 12 bit resolution but
due to hardware tolerances typically span less than their nominal range. with minimum values > 0 and the maximum < 4095. The ABC
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
