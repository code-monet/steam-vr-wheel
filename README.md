# steam-vr-wheel

This fork is a version I modified for personal use only. So it is highly likely that it won't work on other platforms than Quest 2 or alike. If you're, by any chance, inclined to try, download from the releases, since the current commit could be unfunctional.

https://github.com/hjjg200/steam-vr-wheel/assets/18535223/153c2fba-fc47-4f28-8848-c691d39f6034

## Install

Check out the release page and refer to the instruction of the very release you download.

## How to Use

Compatibility of devices other than Quest 2 is not tested.

### Steering Wheel

- Use the `grip` button on your controller to grab and turn the wheel

### H Shifter

[Full demo](https://www.youtube.com/watch?v=mNbI7f03d1Y)

- It has 6 positions + Reverse with Splitter and Range selector
- Grab its knob to change the gear
- When configuring the key of `Gear Position 1` in your game, move from N to 1 to N
- While you are grabbing the knob:
  - Pressing trigger allows you to move the gear to the reverse position
  - Pressing `A` or `X` toggles `Splitter`
  - Pushing `joystick` upwards sets `Range High`
  - Pushing `joystick` downwards sets `Range Low`

### Edit Mode

Triple grip clicks of both the left and right controllers trigger the edit mode. Follow the instructions shown on the console after you enter the edit mode

### Joystick to Buttons

You can configure the behaivor of joystick -- whether it works as button or axis. And you can configure it separately for each direction.

Example 1, if you choose to convert `Left Joy Down` to button, `Left Joy Up` will be solely adjusting the Y axis while `Left Joy Down` acts as a button. Since `Left Joy Left` and `Left Joy Right` are unchanged, they adjust the Z axis together.

Example 2, you can make all 8 directions to buttons; so that you can use them like dpads. In this scenario, Z, Y, RX, RY axes are unused.

|Joystick|Axis|Button ID|
|-|-|-|
|L Left|Z Axis|34|
|L Right|Z Axis|35|
|L Down|Y|36|
|L Up|Y|37|
|R Left|RX|38|
|R Right|RX|39|
|R Down|RY|40|
|R Up|RY|41|

### Bike

WIP


## Example Bindings

### Euro Truck Simulator 2

|Key|Action|
|-|-|
|LT|Clutch (clutch range 95%)|
|RT|Throttle|
|L Joy Click|Attach/Detach Trailer (T)|
|L Joy Left|`Button` Light Modes|
|L Joy Right|`Button` Wiper|
|L Joy Up|`Button` Right Turn Indicator|
|L Joy Down|`Button` Left Turn Indicator|
|R Joy Click|Route Advisor Menu (F1) for pausing game|
|R Joy Left|`Button` Interact (Enter)|
|R Joy Right|`Button` Navigation Mode (F5)|
|R Joy Up|`Button` Parking Brake|
|R Joy Down|`Axis` Brake|
|X|Hazard Warning|
|Y|High Beam|
|A|Cruise Control|
|B|Engine Start/Stop|

- Set `Shifter Toggles Use Switch Mode` to *ON*
- Set `Shifter Layout Behavior` to *Advanced*
- Set `Shifter fast split` to *Clutch press*


## Troubleshooting

Troubleshooting records for the issues I personally experienced.

### Buttons do not register in vJoy monitor app

- It does NOT work on vJoy 2.2.1.1, possibly due to the old version of sdk included in the project.
- Tested working on vJoy 2.1.9.1 ([vJoySetup.exe](https://github.com/jshafer817/vJoy/releases/tag/v2.1.9.1) SHA256: `f103ced4e7ff7ccb49c8415a542c56768ed4da4fea252b8f4ffdac343074654a`)

### Wheel doesn't move in AMS 2

- Controller Damping has to be set to 0, in the section where there are Steering Sensitivity, etc. (not FFB section)

### Overlay images do not show up

- ~~The directory that contains the scripts must not have CJK characters or alike in its path. (Maybe due to encoding process while converting paths to c string)~~
- Non-ASCII characters are now okay to be in the path

## Feature



### Virtual H Shifter

https://github.com/hjjg200/steam-vr-wheel/assets/18535223/861de753-93f5-42fb-8022-0ae159620e7e

It is a h-shifter with 6 positions + reverse, a splitter(A while grabbing knob), and a range selector(Joystick Down or Up while grabbing knob). Press on Trigger to unlock the reverse position

You can select the position of the reverse position in configurator
```text
  1 3 5    R 1 3 5    1 3 5      1 3 5 R
R 2 4 6      2 4 6    2 4 6 R    2 4 6
```



## vJoy Mapping

The below table shows **Quest 2 controller** to vJoy mapping

|Key|Button ID|Note|
|-|-|-|
|Wheel|X Axis|Configure max angle in configurator|
|LT|1|Disabled as default|
|LT Touch|31|Disabled as default|
|L Grip||No mapping|
|LS|4 or 4,5,6,7,8|For VIVE, more trackpad direction option enables the other 4 buttons|
|RT|9|Disabled as default|
|RT Touch|32|Disabled as default|
|R Grip||No mapping|
|RS|12 or 12,13,14,15,16|For VIVE, more trackpad direction option enables the other 4 buttons|
|A|18||
|B|11||
|X|17||
|Y|3||
|L Left|34 or Z Axis||
|L Right|35 or Z Axis||
|L Down|36 or Y Axis||
|L Up|37 or Y||
|R Left|38 or RX||
|R Right|39 or RX||
|R Down|40 or RY||
|R Up|41 or RY||
|Shifter Sequential Pull|46||
|Shifter Sequential Push|45||
|Shifter Position 1|43|When configuring keybind in game, move from N to 1 to N|
|Shifter Position 2|44||
|Shifter Position 3|45||
|Shifter Position 4|46||
|Shifter Position 5|47||
|Shifter Position 6|48||
|Shifter Splitter|49|Grab knob + A|
|Shifter Range Selector|50|Grab knob + Joystick DOWN or UP|
|Shifter Position Reverse|51|Grab knob + Trigger and move to the 7th position|
|Bike Lean Angle|X Axis|Check out all the available bike modes in configurator|
|Bike Throttle|RZ Axis|Turn right controller while pressing grip<br>When configuring keybind in game, increase the throttle beforehand and assign key while it is decreasing|

### Todo

- Make shifter rotatable in space
- Code cleanup
