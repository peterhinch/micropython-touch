# Introduction

This doc serves two purposes:
1. Documenting specific touch drivers.
2. Providing an explanation of the touch calibration process and general design
information.

For setup instructions please see [setup](./SETUP.md).
[Main README](./README.md)

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
2. Allowing for the fact that the physical dimensions of the touch overlay may
exceed those of the pixel array. In this case, as points on the pixel array are
touched, the range of values from the touch controller is smaller than its
theoretical 0-4095 bits. Calibration enables the touch driver base class to
correct for this.
3. Mapping `(x,y)` touch coordinates onto `(row,col)` screen coordinates. This
must allow for landscape/portrait or upside down orientation. For example, if a
display has 240x320 pixels and is mounted in portrait mode, a touch near the top
left corner will issue something close to `row=0, col=0`. A touch near the
bottom right will issue something close to `row=319, col=239`.

The output of the calibration process is a line of code defining values for the
touchpad driver's `init` method. This is documented below.

Determining the long axis is possible because the `touch` constructor takes as
an arg the  initialised display driver instance: the code can deduce the long
axis from `ssd.height` and `ssd.width` (the pixel dimensions). Orientation can
be deduced because `touch.setup` prompts the user to touch points in a specific
order.

# TSC2007

Constructor. This takes the following positional args:
* `i2c` An initialised I2C bus. Baudrate should be 100_000.
* `ssd` Initialised display driver instance.
* `addr=0x48` I2C address of device.

Optional keyword-only arg:
* `alen:int=10`
This determines the post-processing done on touch samples. When a touch occurs a
set of N samples is acquired and the mean is taken as the touch location. `alen`
determines the size of the set.

Method: `init`. This is a method of the base class and its args are described
below in "the init method". In practice the user runs the calibration script
`touch.setup.py` which outputs a line of code such as
```python
tpad.init(240, 320, 241, 292, 3866, 3887, True, True, False)
```
This is pasted into `touch_setup.py`.

# XPT2046

Constructor. This takes the following mandatory positional args:
* `spi` An initialised SPI bus. Baudrate 2.5MHz max.
* `cspin` An initialised `Pin` instance connected to the device chip select.
* `ssd` Initialised display driver instance.

Optional keyword-only arg:
* `alen:int=10`
This determines the post-processing done on touch samples. When a touch occurs a
set of N samples is acquired and the mean is taken as the touch location. `alen`
determines the size of the set.

Method: `init`. This is a method of the base class and its args are described
below in "the init method". In practice the user runs the calibration script
`touch.setup.py` which outputs a line of code such as
```python
tpad.init(240, 320, 241, 292, 3866, 3887, True, True, False)
```
This is pasted into `touch_setup.py`.

# FT6206 Capacitive controller

`FT6206` constructor mandatory positional args:
* `i2c` An initialised I2C bus. Baudrate should be 400_000 max.
* `ssd` Initialised display driver instance.

Optional args:
* `addr=0x38` I2C address of device.
* `thresh=128` Touch detection threshold.

The example tested was [Adafruit 2.8" touch shield](https://www.adafruit.com/product/1947).
The FT6206 produced pre-calibrated row and column values which did not need
calibration or pre-processing. Calibration should still be performed to enable
screen orientation to be detected. The `.init` method ignores the last four
numeric args as scaling is not required.

See `setup_examples/ili9341_ft6206_pico.py`.

# CST816S Capacitive controller

`CST816S` class.  
Constructor mandatory positional args:
* `i2c` An initialised I2C bus. Baudrate should be 400_000 max.
* `rst` A `Pin` instance initialised with `Pin.OUT, value=1`.
* `pint` A `Pin` instance initialised with `Pin.IN`.
* `ssd` Initialised display driver instance.

Optional arg:
* `addr=0x15` I2C address of device.

Bound variable:
* `version` Returns the chip version information. See technical note below and
code comments.

See `setup_examples/gc9a01_ws_rp2040_touch.py` for a `touch_setup.py`
example. Note that `touch.setup.py` is unusable with circular
displays because the crosses lie outside the visible area. However the
controller is pre-calibrated and the following initialisation should be used:
```py
tpad.init(240, 240, 0, 0, 240, 240, False, True, True)
```
The three boolean args are described below and may be changed to match the
orientation of the screen (to validate run `touch.check`).

Tested with [Waveshare 1.28 inch touch LCD](https://www.waveshare.com/wiki/1.28inch_Touch_LCD)
and [Waveshare RP2040 touch LCD 1.28](https://www.waveshare.com/wiki/RP2040-Touch-LCD-1.28).

### Technical note

The chip has the curious property of being undetectable by `I2C.scan`. It only
becomes present on the I2C bus for a "brief period" after it issues an
interrupt. It is also poorly documented, with the above "brief period" being
unknown. This ha the weird consequence that it is impossible to check the chip's
presence and version details until after it has detected a touch and raised an
interrupt. If anyone can shed any light on this, please raise an issue.

# CST820 Capacitive controller

`CST820` class.  
Constructor mandatory positional args:
* `i2c` An initialised I2C bus. Baudrate should be 400_000 max.
* `rst` A `Pin` instance initialised with `Pin.OUT, value=1`.
* `ssd` Initialised display driver instance.

Optional arg:
* `addr=0x15` I2C address of device.

Bound variable:
* `version` Returns the chip version information. See technical note below and
code comments.

See `setup_examples/gc9a01_ws_rp2040_touch.py` for a `touch_setup.py`
example. Note that `touch.setup.py` is unusable with circular
displays because the crosses lie outside the visible area. However the
controller is pre-calibrated and the following initialisation should be used:
```py
tpad.init(240, 240, 0, 0, 240, 240, False, True, True)
```
The three boolean args are described below and may be changed to match the
orientation of the screen (to validate run `touch.check`).

# Under the hood

The following provides details for those wishing to adapt the code or to
contribute new touch drivers.

## Design

Touchscreen hardware comes in various forms requiring different drivers. All
drivers are subclassed from `ABCTouch` defined in `touch.touch.py`. This
abstract base class performs coordinate scaling to handle calibration values,
also reflection and rotation for landscape/portrait or USD configuration. It
also does averaging to reduce the noise present in touch measurements. This
enables hardware specific subclasses to be extremely minimal, simplifying the
development of further drivers. Currently three drivers are provided:
* TSC2007 [e.g. Adafruit](http://www.adafruit.com/products/5423)
* XPT2046 Used on many Chinese resistive touchscreens.
* FT6206 [e.g. Adafruit](https://www.adafruit.com/product/1947).

## Mapping

The `x` and `y` values have 12 bit resolution but due to hardware tolerances
typically span less than their nominal range. In general minimum values are
greater than 0 and the maximum is less than 4095. The ABC compensates for these
limitations and performs mapping from `(x, y)` to `(row, col)` in accordance
with the display orientation (e.g. landscape/portrait, usd, etc.).

## API: The init method

This base class method takes the following mandatory positional arguments:
1. `xpix: int` Number of pixels associated with `x` coordinate.
2. `ypix: int` Number of pixels associated with `y` coordinate.
3. `xmin: int` Minimum value of `x`. These four values are for scaling.
4. `ymin: int` Minimum value of `y`.
5. `xmax: int` Maximum  value of `x`.
6. `ymax: int` Maximum value of `y`.
7. `trans:bool` Transpose axes.
8. `rr:bool` Reflect rows.
9. `rc:bool` Reflect columns.

The calibration procedure provides all these args.

### poll

This base class method is periodically called by the GUI. It takes no args and
returns `True` if the screen is touched. In this case the touch coordinates in
pixels may be retrieved from `.row` and `.col` bound variables.

Signals from touch overlays are noisy. A `PreProcess` object aims to reduce
noise. The `poll` method calls the preprocessor's `get` method. If this returns
`True`, smoothed touch coordinates may be accessed in the `._x` and `._y` bound
variables. If the `get` method returns `False`, `poll` should return `False` and
the GUI will ignore the touch.

Internally the pre-processor calls the `acquire` method of the subclass. It may
do this multiple times before returning a result. The `get` and `acquire`
methods may raise an `OSError`: this is trapped by the GUI and the touch is
rejected.

If `get` returns `True` the `poll` method converts the raw xy coordinates to
pixel values, updating `.row` and `.col`. In this case `poll` returns `True` and
the GUI accepts the touch.

### acquire

This method of the superclass is the hardware interface. It returns a `bool`
indicating if a touch was in progress when called. If so, the base class
`._x` and `._y` bound variables are updated with the raw values from the
hardware. The method can also throw an `OSError` if the hardware produces an
invalid response. This is trapped by the GUI and the touch is ignored.

### The preprocessor

The use of a separate preprocessor object allows for the possibility of using a
different algorithm with an individual hardware driver. The preprocessor is
instantiated in the hardware driver's constructor, and takes args provided to
the driver's constructor.

The currently implemented `PreProcess` class (in `touch.py`) works as follows.

Constructor args:
* `tpad` The `Touch` instance.
* `alen:int` Array length: number of samples to acquire.

When the `get` method is called, arrays `.ax` and `.ay` are populated by
repeated calls to the superclass `acquire`. The mean values of x and y are
calculated.

If the touch ends before a full sample set is acquired, `get` returns `False`
and no touch is recorded. Otherwise `get` returns `True` and the ABC bound
variables `._x` and `._y` are updated to contain the mean values of the raw
touch coordinates.

There is also a `NoPreProcess` class for pre-calibrated displays. This simply
passes `get` calls to `acquire`.
