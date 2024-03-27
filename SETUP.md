# Setting up a touch display

[Main README](./README.md)

# 1. Defining the approach

## 1.1 Choosing hardware

### 1.1.1 Screen

Touch screens vary considerably in quality. Manufacturers such as Adafruit make
good quality displays: a sustained touch at a fixed location produces readings
with a high level of consistency. Further, they produce consistent results over
the entire surface with no dead zones.Chinese units can be cheap but produce
noisy outputs. [This Adafruit screen](https://www.adafruit.com/product/1743) was
used in development with [this touch controller](http://www.adafruit.com/products/5423)
with good results.

### 1.1.2 Platform

The principal issue is RAM. The amount required by an application depends on a
number of factors including display pixel count and color depth; also the
complexity and number of application screens. There is great scope for reducing
RAM requirements by using frozen bytecode (or
[romfs](https://github.com/micropython/micropython/pull/8381) when it arrives).
Fonts in particular use almost zero RAM when located in Flash. As a general
pointer the Pico runs all demos with no use of frozen code and plenty of free
RAM. On the Pico W, free RAM on the more complex demos is limited.

## 1.2 Development approach

It is suggested that the official
[mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html) is
used. This can be employed in a way that avoids installing anything on the
target with the advantage that the entire GUI with all device drivers is
available at the outset.

The repository is cloned to the PC. The hardware definition file in the root of
the repo tree is edited to match the user hardware. The application is put in
the same directory and run from there. The application is deployed to the
hardware relatively late in its development, accompanied by that subset of the
GUI repo required for its operation. See [deployment](./SETUP.md#3-deployment).

An alternative is the traditional approach of deploying at the outset. This may
make sense on platforms where the USB interface is slow. Loading times are
reduced when files are in Flash rather than on the PC.

# 2. Quick start

Setup comprises the following steps:
1. Cloning the repo.
2. Writing a `hardware_setup.py` file. This defines the display interface. It
imports the correct device driver for the display, then defines `Pin` objects
for the display's control signals and defines a hardware SPI bus for the screen.
The display driver constructor creates a global `ssd` instance. Constructor args
assign the interface elements and define the orientation of the screen
(portrait, landscape, upside-down (USD) which should be chosen to match project
requirements.
3. Testing and confirming orientation by running a simple script.
4. Modifying `hardware_setup.py` to add a touchscreen definition. Typically this
is an I2C or SPI interface, in some cases with additional `Pin` objects. The
interface may be hard or soft as speeds are relatively low.
5. Calibrating the touchscreen. This involves running a script, touching objects
on screen, and pasting a line of code into `hardware_setup.py`.
6. Confirming operation using one or more of the supplied demo scripts.

The following describes those steps in detail. Assumptions are that `mpremote`
is used to mount the PC directory and that hardware consists of a Pico with
ILI9341 display and TSC2007 touch controller.

## 2.1 Clone the repo

Choose a working directory on the PC and issue:
```bash
$ git clone https://github.com/peterhinch/micropython-touch/tree/master
```
Change to the `micropython-touch` directory.

## 2.2 Edit hardware_setup.py

See examples in the `setup_examples` directory.

Edit this file to match your hardware. Initially the aim is to configure the
display, so there is no reference to the touch panel. Typical contents are as
follows:
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

from gui.core.tgui import Display, quiet
quiet()  # Suppress free RAM messages (optional)
display = Display(ssd)
```
The `Pin` instances are arbitrary, but the SPI instance should be hard SPI with
the maximum baudrate permitted by the display driver chip. The bus should not be
shared with any other device.

Args to `SSD` should be chosen to match the display dimensions in pixels and the required
orientation (landcsape/portrait etc.) See
[display drivers doc.](https://github.com/peterhinch/micropython-nano-gui/blob/master/DRIVERS.md).

## 2.3 Test the display

Run `mpremote` as follows:
```bash
$ mpremote mount .
```
At the REPL paste the following (ctrl-e, ctrl-v, ctrl-d):
```python
from hardware_setup import ssd  # Create a display instance
from gui.core.colors import *
ssd.fill(0)
ssd.line(0, 0, ssd.width - 1, ssd.height - 1, GREEN)  # Green diagonal corner-to-corner
ssd.rect(0, 0, 15, 15, RED)  # Red square at top left
ssd.rect(ssd.width -15, ssd.height -15, 15, 15, BLUE)  # Blue square at bottom right
ssd.show()
```
With the display oriented as per the project requirements, it should show a red
square at the top left, a blue square at bottom right, and a green diagonal line
passing through the squares. This should be pixel perfect.

## 2.4 Add the touch overlay

Exit the REPL with `ctrl-x`. Edit `hardware_setup.py` to add the touch
controller. In the case of TSC2007 replace the last line
(`display = Display(ssd)`) with the following (pin numbers may be adapted):
```python
from touch.tsc2007 import TSC2007
i2c = SoftI2C(scl=Pin(27), sda=Pin(26), freq=100_000)
tpad = TSC2007(i2c, ssd)
display = Display(ssd, tpad)
```
See [touchpad doc](./TOUCHPAD.md) for other touch controllers.

Hard or soft I2C may be used. Note that I2C interfaces require pullup resistors.
In many cases these are installed on the target hardware.

Touch controllers such as XPT2046 use an SPI bus. This may be hard or soft and
speed is not critical. The SPI bus may not be shared with that of the display.

## 2.5 Touch calibration

Run `mpremote mount .` as before. At the REPL issue
```python
>>> import touch.setup
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
`hardware_setup.py` as below:
```python
from touch.tsc2007 import TSC2007
i2c = SoftI2C(scl=Pin(27), sda=Pin(26), freq=100_000)
tpad = TSC2007(i2c, ssd)
tpad.init(240, 320, 120, 314, 3923, 3878, True, True, False)  # Extra line
display = Display(ssd, tpad)
```

After a reboot the touch interface should work. A script `touch.check` provides
optional confirmation. At the REPL issue:
```python
>>> import touch.check
```
and touch various points on the screen with a stylus. Reported `row` and `col`
coordinates should be near zero at the top left, increasing to close to the
display's pixel dimensions as touch is moved from downwards and to the right.

## 2.6 Final confirmation

At the REPL reset the hardware (with `ctrl-d`) and issue:
```python
>>> import gui.demos.simple
```
This should show two `Button` widgets labelled "Yes" and "No". When they are
touched, output should appear at the REPL.

## 2.7 Troubleshooting

If a screen proves hard to calibrate it can be informative to run `touch.check`
on the uncalibrated screen. Comment out any `tpad.init` line in
`hardware_setup.py`, reboot and run the test. Ignore the `row` and `col` values.
The `x` and `y` values should vary smoothly as a touch is moved across the
display. Values should start around 0 to the low hundreds and end within a few
hundred of 4095. If there are dead zones where the value of an axis barely
changes as the touch is moved, the touch overlay is not usable. 

# 3. Deployment

This is for two scenarios:
* A completed application is to be deployed to the hardware.
* The developer has opted to locate files on the hardware rather than mounting
the PC directory with `mpremote`.

Move to the `micropython-touch` directory on the PC. Issue
```bash
$ mpremote mip install "github:peterhinch/micropython-touch"
```
This installs a minimal subset of the GUI to the hardware, enabling all the
steps described above to be accomplished. The filesystem on the device will be
similar to this (under the `/lib` directory):  
![Image](./images/filesystem.png)  

Note that the display driver for ILI9341 is installed. If a different driver is
required, see
[the drivers doc](https://github.com/peterhinch/micropython-nano-gui/blob/master/DRIVERS.md#12-installation).

To setup a system with files on the device follow the above instructions,
ensuring that after each edit of `hardware_setup.py` the file is copied to the
device:
```bash
$ mpremote cp hardware_setup.py :
```
Where a completed application is to be deployed it is necessary to copy all
fonts, widgets and bitmaps employed by the application.

## 3.1 Freezing bytecode

Substantial RAM savings may be achieved using this technique. Please see
[Appendix 2 Freezing bytecode](./README.md#appendix-2-freezing-bytecode) in the
main README.
