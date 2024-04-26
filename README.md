# steam-vr-wheel

This fork is a version I modified for personal use only. So it is highly likely that it won't work on other platforms than Quest 2 or alike. If you're, by any chance, inclined to try, download from the releases, since the current commit could be unfunctional.

https://github.com/hjjg200/steam-vr-wheel/assets/18535223/153c2fba-fc47-4f28-8848-c691d39f6034

- [Full demo](https://www.youtube.com/watch?v=aCCVCgAIRPM)

## Memo

Qyuest 2 vJoy mapping, configure vJoy device to have more than 50 buttons and all axes enabled

|Key|Button ID|Note|
|-|-|-|
|LT|1||
|LT Touch|31||
|L Grip|2|Disabled|
|LS|4 or 4,5,6,7,8||
|RT|9||
|RT Touch|32||
|R Grip|10|Disabled|
|RS|12 or 12,13,14,15,16||
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
|Shifter Position 1|43||
|Shifter Position 2|44||
|Shifter Position 3|45||
|Shifter Position 4|46||
|Shifter Position 5|47||
|Shifter Position 6|48||
|Shifter Splitter|49|Grab knob + Trigger(layout 1) or A(layout 2)|
|Shifter Range Selector|50|Grab knob + Joystick DOWN or UP|

### Troubleshooting

Troubleshooting records for the issues I personally experienced.

#### Overlay images do not show up

- The directory that contains the scripts must not have CJK characters or alike in its path. (Maybe due to encoding process while converting paths to c string)

#### Buttons do not register in vJoy monitor app

- It does NOT work on vJoy 2.2.1.1, possibly due to the old version of sdk included in the project.
- Tested working on vJoy 2.1.9.1 (vJoySetup.exe SHA256: f103ced4e7ff7ccb49c8415a542c56768ed4da4fea252b8f4ffdac343074654a)

### Todo

- Make shifter rotatable in space
- Shifter degrees x and z
- Code cleanup

### Config memo

Memos for \*original\* config behaviors. Some configs' behaviors are changed as I don't have Vive controllers to test the behavior

|Config|Module|Behavior|
|-|-|-|
|Triggers pre press button|`VirtualPad`|Touching trigger registers|
|Triggers press button|`VirtualPad`|Trigger press registers along with axis change|
|5 Button touchpad|`VirtualPad`|On Quest 2 controller, the axis values determine button id|
|Haptic feedback for trackpad button zones|`VirtualPad`|Haptic when 5-button button id changed|
|Touchpad mapping to axis while untouched (axis move to center when released)|`VirtualPad`||
|Steering wheel is vertical|`Wheel`||
|Joystick moves only when grabbed (by right grip)|`Joystick`||
|Joystick grab is a switch|`Joystick`||
|Layout edit mode|`Wheel`||
|Manual wheel grabbing|`Wheel`||
|Continuous (index, checked) or toggle (vive) wheel gripping|`Wheel`||
|Show Wheel Overlay|`Wheel`||
|Show Hands Overlay|`Wheel`||

Changed(applied or planned) behavior:

|Config|Behavior|
|-|-|
|Triggers pre press button|Set default to disabled|
|Triggers press button||
|5 Button touchpad|Disabled as default, more description|
|Haptic feedback for trackpad button zones|Disabled as default, more description|
|Touchpad mapping to axis while untouched (axis move to center when released)|Disabled, since joysticks are handlded differently now|
|Steering wheel is vertical|Disabled, the wheel will be manually rotatable in edit mode|
|Joystick moves only when grabbed (by right grip)|Hidden; use the original version for better experience|
|Joystick grab is a switch|Hidden|
|Layout edit mode|Disabled, users have to enter edit mode by triple grip clicks|
|Manual wheel grabbing||
|Continuous (index, checked) or toggle (vive) wheel gripping||
|Show Wheel Overlay||
|Show Hands Overlay||

## This fork

### Comaptibility

- Compatibility of devices other than Quest 2 is not tested.
- Only the wheel mode(wheel.bat) is tested.

### Edit Mode

Triple grip clicks of both the left and right controllers trigger the edit mode.

Move your RIGHT controller to the center of the wheel and press the trigger on RIGHT controller; while holding down:
- Resize: Move RIGHT joystick up and down to resize the wheel.
- Transparency: Press B button to cycle through the transparency mode.
- Align Center: Press A button to align the wheel to center.

Move your RIGHT controller to the knob of the shifter to adjust its position.

Pressing the grip on RIGHT exits the edit mode.

### Quest 2's Joystick to Buttons

You can convert all direcitons of the joysticks to buttons or leave it as axis.

Example 1, if you choose to convert the Left Joy Down to button, Left Joy Left and Left Joy Right will remain as the same axis; the Left Joy Up will be solely adjusting the axis while the Left Joy Down acts as a button.

Example 2, you can make all 8 directions to buttons; so that you can use them like dpads.

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

### Virtual H Shifter

https://github.com/hjjg200/steam-vr-wheel/assets/18535223/861de753-93f5-42fb-8022-0ae159620e7e

It is a h-shifter with 6 positions, a splitter(A while grabbing knob), and a range selector(Trigger while grabbing knob).

```text
1 3 5
2 4 6
```
|Key|Button ID|Note|
|-|-|-|
|Position 1|43||
|Position 2|44||
|Position 3|45||
|Position 4|46||
|Position 5|47||
|Position 6|48||
|Splitter|49|Grab knob + Trigger or A|
|Range Selector|50|Grab knob + Joystick down or up|

Buttons for splitter and range selector have two layouts: 1. splitter=trigger range=A 2. splitter=A range=B
