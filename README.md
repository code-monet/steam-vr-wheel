# steam-vr-wheel

### Fork memo

This will likely work only with Quest 2 controllers. And only the wheel mode work properly.

Qyuest 2 vjoy mapping
|Key|No|
|-|-|
|LT|1|
|L Grip|2|
|RT|9|
|R Grip|10|
|A|18|
|B|11|
|X|17|
|Y|3|

This fork aims to convert each joystick to 4-way button
|Key|No|
|-|-|
|LX|4,5|
|LY|6,7|
|RX|13,14|
|RY|15,16|

Added features
- Edit mode
  - Triple grip click on right controller toggles wheel edit mode
  - Single grip click on right exits edit mode
  - A sets wheel X value to 0
  - B switches alpha of wheel with a step of 10%
- L joystick and R joystick to buttons; total 8 buttons


Wheel emulation using steamVR
=============================



News
=============================
I've got a wheel and hotas recently, and haven't had much time to work on this anyway. It will continue to work thanks to SteamVR good backward compatability, but don't expect any further updates. If anyone wants to fork and keep developing maintaining this app, they are free to do so under MIT licence.


If you just want to use this go to:
===================================
https://github.com/mdovgialo/steam-vr-wheel/releases


For developers:
================

Requires pyopenvr, wxpython (codename phoenix), and vjoy ( http://vjoystick.sourceforge.net/site/ Public domain )

Uses pyvjoy binding from https://github.com/tidzo/pyvjoy

Demos:
======

Wheel mode:
https://www.youtube.com/watch?v=lb0zGBVwN4Y

Joystick mode:
https://www.youtube.com/watch?v=jjb92HQ0M74






Instalation from sources (for developers):
========================================
install python 3.5+

install vjoy

with admin level cmd go to folder where is steam_vr_wheel

write:

pip install .




To run:
=======
open cmd, write:

vrwheel

or 

vrjoystick

or 

vrpad

For configurator - write

vrpadconfig

press ctrl+c to stop

To uninstall:

pip uninstall steam_vr_wheel

