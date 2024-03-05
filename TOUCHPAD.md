# Touchscreen interface

Touchscreen hardware comes in various forms requiring different drivers. The aim
is that all drivers are subclassed from an abstract base class (ABC) defined in
`touch.touch.py`. This should ensure that all drivers present a common API.
Touch drivers written for this GUI are minimal, offering only the functionality
required by the GUI.

## Coordinates

To avoid confusion, values returned by the hardware driver are referred to as `x`
and `y`, while pixel values are `row` and `col`. Typically `x` and `y` values
might have 12 bit resolution and, due to hardware tolerances, may span less than
their nominal range with minimum values > 0 and the maximum < 4095. The ABC
compensates for these limitations and performs mapping from `(x, y)` to
`(row, col)` in accordance to the display orientation (e.g. landscape/portrait,
usd, etc.).

Two test scripts simplify the adaptation of `hardware_setup.py` to match touch
to the display.

# Touch panel API

## Constructor

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

# Setting up a touchpad

## Configuring hardware

This has two aims:
1. Determine calibration values for the touchpad.
2. Assign pixel dimensions to the driver such that the physical long and short
axes are respected.

This is done by running `touch.hwtest.py`. This takes the `hardware_setup.py`
file as input and produces a corrected set of argument values for the touch
panel constructor. Initially `hardware_setup.py` should have a basic constructor
call e.g.
```python
tpad = TSC2007(i2c, 320, 240)  # Order of height and width don't matter at this stage
```
Run the script:
```python
>>> import touch.hwtest
```
then touch the screen. A coordinate pair should be printed. As the point of
touch is moved, x and y values should change. Slowly move the point of contact
until it crosses each of the four boundaries of the display. Note whether moving
along the long axis of the display causes change in x or y. Finally interrupt
the script with `ctrl-c`. The script will output two sets of constructor args.
Choose the set of args matching the observed long axis, then copy and paste them
into `hardware_setup.py`.

## Configuring software

The aim here is to define args for `tpad.mapping()` in `hardware_setup.py`. To
do this the display should be mounted as intended in the application: `row` and
`col` values should be near zero at the top left hand corner of the screen, with
`row` increasing as the touch point moves down, and `col` increasing as it moves
to the right.

The script is run with
```python
>>> import touch.swtest
```
The script provides usage instructions.

If transposition is required `hardware_setup.py` should be edited to set
```python
tpad.mapping(transpose=True)
```
The platform should be reset and the script run again to determine whether the
`row_reflect` or `col_reflect` args need to be set.
After each run of the script, `hardware_setup.py` should be edited and the
platform reset.
