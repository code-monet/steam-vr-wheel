# steam-vr-wheel

This fork is a version I modified for personal use only. So it is highly likely that it won't work on other platforms than Quest 2 or alike. If you're, by any chance, inclined to try, download from the releases, since the current commit could be unfunctional.

## Memo

Qyuest 2 vJoy mapping

|Key|Button ID|Note|
|-|-|-|
|LT|1||
|L Grip|2|Disabled|
|LS|4||
|RT|9||
|R Grip|10|Disabled|
|RS|12||
|A|18||
|B|11||
|X|17||
|Y|3||
|Left Touch|31|Disabled|
|Right Touch|32|Disabled|

### Todo

- Make controlling of shifter more intuitive
- Left handed shifter
- Fast split and range select mode: A button to split and trigger to range select
- Clean up unused configs
- Code cleanup

## This fork

### Comaptibility

- Compatibility of devices other than Quest 2 is not tested.
- Only the wheel mode(wheel.bat) is tested.
- Manual grabbing(wheel configuration) is recommended.

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

```text
<Video Demo>
```

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
|Neutral|42||
|Splitter|49|Grab knob and A|
|Range Selector|50|Grab knob and Trigger|
