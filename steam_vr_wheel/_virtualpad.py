import sys

import openvr
import time

from steam_vr_wheel.configurator import ConfiguratorApp
from steam_vr_wheel.pyvjoy.vjoydevice import VJoyDevice, HID_USAGE_SL0, HID_USAGE_SL1, HID_USAGE_X, HID_USAGE_Y, HID_USAGE_Z, HID_USAGE_RX, HID_USAGE_RY
from steam_vr_wheel.vrcontroller import Controller
from . import PadConfig, ConfigException
import multiprocessing

BUTTONS = {}
BUTTONS['left'] = {openvr.k_EButton_ApplicationMenu: 3, #openvr.k_EButton_Grip: 2,
                     openvr.k_EButton_SteamVR_Touchpad: -1, # 4 5 6 7 8
                   openvr.k_EButton_SteamVR_Trigger: 1, openvr.k_EButton_A: 17,
                   }
BUTTONS['right'] = {openvr.k_EButton_ApplicationMenu: 11, #openvr.k_EButton_Grip: 10,
                     openvr.k_EButton_SteamVR_Touchpad: -2, # 12 13 14 15 16
                    openvr.k_EButton_SteamVR_Trigger: 9, openvr.k_EButton_A: 18
                    }

AXES = {}
AXES['left'] =  {'left-right': HID_USAGE_Z, 'down-up': HID_USAGE_Y, 'trigger': HID_USAGE_SL0}
AXES['right'] = {'left-right': HID_USAGE_RX, 'down-up': HID_USAGE_RY, 'trigger': HID_USAGE_SL1}
AXES_BASE_HID = {}
AXES_BASE_HID['left'] =  {'left-right': 34, 'down-up': 36}
AXES_BASE_HID['right'] = {'left-right': 38, 'down-up': 40}

DISABLED_BUTTONS = {}
DISABLED_AXES = {}


class LeftTrackpadAxisDisablerMixin:
    trackpad_left_enabled = False


class RightTrackpadAxisDisablerMixin:
    trackpad_right_enabled = False


def run_configurator():
    ConfiguratorApp().run()


class VirtualPad:
    trackpad_left_enabled = True
    trackpad_right_enabled = True
    def __init__(self):
        self.init_config()
        device = 1
        try:
            device = int(sys.argv[1])
        except:
            print('selecting default')
            pass
        self.device = VJoyDevice(device)
        self.trackpadRtouch = False
        self.trackpadLtouch = False
        self.trackpadLX = 0
        self.trackpadLY = 0
        self.trackpadRX = 0
        self.trackpadRY = 0
        self.sliderL = 0
        self.sliderR = 0

        self.previous_left_zone = 0
        self.previous_right_zone = 0

    def init_config(self):
        config_loaded = False
        app_ran = False
        while not config_loaded:
            try:
                self.config = PadConfig()
                config_loaded = True
            except ConfigException as e:
                print(e)
                if not app_ran:
                    p = multiprocessing.Process(target=run_configurator)
                    p.start()
                    app_ran = True
                time.sleep(1)

    def get_trackpad_zone(self, right=True):
        if self.config.multibutton_trackpad:
            if right:
                X, Y = self.trackpadRX, self.trackpadRY
            else:
                X, Y = self.trackpadLX, self.trackpadLY
            zone = self._get_zone(X, Y) + right * 8 + 4
        else:
            zone = 0 + right * 8 + 4
        return zone

    def _get_zone(self, x, y):
        if (x**2 + y**2)**0.5 <0.3:
            return 0
        if x>y:
            if y>(-x):
                return 1
            else:
                return 2
        if x<y:
            if y<(-x):
                return 3
            else:
                return 4

    def set_button(self, btn_id, val):
        if btn_id in DISABLED_BUTTONS:
            return
        self.device.set_button(btn_id, val)

    def set_axis(self, axis_id, val):
        if axis_id in DISABLED_AXES:
            return
        self.device.set_axis(axis_id, val)

    def enable_all(self):
        DISABLED_BUTTONS = {}
        DISABLED_AXES = {}

    def enable_button(self, hand, button):
        btn_id = BUTTONS[hand][button]
        del DISABLED_BUTTONS[btn_id]

    def disable_button(self, hand, button):
        btn_id = BUTTONS[hand][button]
        DISABLED_BUTTONS[btn_id] = True
        self.device.set_button(btn_id, False)

    def enable_axis(self, hand, axis):
        axis_id = AXES[hand][axis]
        del DISABLED_AXES[axis_id]

        if axis in AXES_BASE_HID[hand]:
            b = AXES_BASE_HID[hand][axis]
            del DISABLED_BUTTONS[b]
            del DISABLED_BUTTONS[b+1]

    def get_axis_zero(self, hand, axis):
        btns = self.axis_buttons(hand, axis)
        zero = 0.0 if btns[0] or btns[1] else 0.5
        return zero

    def disable_axis(self, hand, axis):
        axis_id = AXES[hand][axis]
        DISABLED_AXES[axis_id] = True
        zero = self.get_axis_zero(hand, axis)
        self.device.set_axis(axis_id, int(zero * 0x8000))

        if axis in AXES_BASE_HID[hand]:
            b = AXES_BASE_HID[hand][axis]
            DISABLED_BUTTONS[b] = True
            DISABLED_BUTTONS[b+1] = True

    def axis_buttons(self, hand, axis):
        AXES_BUTTONS = {}
        AXES_BUTTONS['left'] = {'left-right': [self.config.j_l_left_button, self.config.j_l_right_button],
                                'down-up': [self.config.j_l_down_button, self.config.j_l_up_button],
                                'trigger': [True, True]}
        AXES_BUTTONS['right'] = {'left-right': [self.config.j_r_left_button, self.config.j_r_right_button],
                                'down-up': [self.config.j_r_down_button, self.config.j_r_up_button],
                                'trigger': [True, True]}
        return AXES_BUTTONS[hand][axis]

    def pressed_left_trackpad(self):
        btn_id = self.get_trackpad_zone(right=False)
        self.set_button(btn_id, True)

    def unpressed_left_trackpad(self):
        for btn_id in [4, 5, 6, 7, 8]:
            try:
                self.set_button(btn_id, False)
            except NameError:
                pass

    def pressed_right_trackpad(self):
        btn_id = self.get_trackpad_zone(right=True)
        self.set_button(btn_id, True)

    def unpressed_right_trackpad(self):
        for btn_id in [12, 13, 14, 15, 16]:
            try:
                self.set_button(btn_id, False)
            except NameError:
                pass

    def set_button_press(self, button, hand):
        if button == openvr.k_EButton_SteamVR_Trigger:
            if not self.config.trigger_press_button:
                return
        try:
            btn_id = BUTTONS[hand][button]
            if btn_id is None:
                return
            if btn_id == -1:
                self.pressed_left_trackpad()
            elif btn_id == -2:
                self.pressed_right_trackpad()
            else:
                self.set_button(btn_id, True)
                
        except KeyError:
            pass

    def set_button_unpress(self, button, hand):
        try:
            btn_id = BUTTONS[hand][button]
            if btn_id == -1:
                self.unpressed_left_trackpad()
            elif btn_id == -2:
                self.unpressed_right_trackpad()
            else:
                self.set_button(btn_id, False)
        except KeyError:
            pass

    def set_trigger_touch_left(self):
        if self.config.trigger_pre_press_button:
            self.set_button(31, True)

    def set_trigger_touch_right(self):
        if self.config.trigger_pre_press_button:
            self.set_button(32, True)

    def set_trigger_untouch_left(self):
        self.set_button(31, False)

    def set_trigger_untouch_right(self):
        self.set_button(32, False)

    def set_trackpad_touch_left(self):
        self.trackpadLtouch = True

    def set_trackpad_touch_right(self):
        self.trackpadRtouch = True

    def set_trackpad_untouch_left(self):
        self.trackpadLtouch = False

    def set_trackpad_untouch_right(self):
        self.trackpadRtouch = False

    def _check_zone_change(self, zone, prev_zone):
        # check config, return False
        if self.config.multibutton_trackpad and self.config.multibutton_trackpad_center_haptic:
            if prev_zone != zone:
                return True
        return False

    def update(self, left_ctr: Controller, right_ctr: Controller, hmd: Controller):
        self.set_axis(HID_USAGE_SL0, int(left_ctr.axis * 0x8000))
        self.set_axis(HID_USAGE_SL1, int(right_ctr.axis * 0x8000))

        haptic_pulse_strength = 1000
        DEADZONE_DPAD = 0.9
        """
        |LX|34,35|
        |LY|36,37|
        |RX|38,39| 
        |RY|40,41|
        """
        def convert_axis(trackpad, hand, axis):

            axis_hid = AXES[hand][axis]
            base_hid = AXES_BASE_HID[hand][axis]
            btns = self.axis_buttons(hand, axis)

            if btns[0] or btns[1]:
                amount = abs(trackpad)
                zero = 0
            else:
                amount = trackpad+1 / 2
                zero = 0.5

            plus_dead = DEADZONE_DPAD if btns[1] else 0.1
            minus_dead = -DEADZONE_DPAD if btns[0] else -0.1

            if trackpad <= minus_dead:
                if btns[0]:
                    self.set_button(base_hid, True)
                else:
                    self.set_axis(axis_hid, int(amount * 0x8000))
            elif trackpad >= plus_dead:
                if btns[1]:
                    self.set_button(base_hid+1, True)
                else:
                    self.set_axis(axis_hid, int(amount * 0x8000))
            else:
                if btns[0]:
                    self.set_button(base_hid, False)
                else:
                    self.set_axis(axis_hid, int(zero * 0x8000))
                if btns[1]:
                    self.set_button(base_hid+1, False)
                else:
                    self.set_axis(axis_hid, int(zero * 0x8000))

        self.trackpadLX = left_ctr.trackpadX
        self.trackpadLY = left_ctr.trackpadY

        left_zone = self._get_zone(self.trackpadLX, self.trackpadLY)
        crossed = self._check_zone_change(left_zone, self.previous_left_zone)
        self.previous_left_zone = left_zone
        if crossed:
            openvr.VRSystem().triggerHapticPulse(left_ctr.id, 0, haptic_pulse_strength)

        convert_axis(left_ctr.trackpadX, 'left', 'left-right')
        convert_axis(left_ctr.trackpadY, 'left', 'down-up')

        self.trackpadRX = right_ctr.trackpadX
        self.trackpadRY = right_ctr.trackpadY

        right_zone = self._get_zone(self.trackpadRX, self.trackpadRY)
        crossed = self._check_zone_change(right_zone, self.previous_right_zone)
        self.previous_right_zone = right_zone
        if crossed:
            openvr.VRSystem().triggerHapticPulse(right_ctr.id, 0, haptic_pulse_strength)

        convert_axis(right_ctr.trackpadX, 'right', 'left-right')
        convert_axis(right_ctr.trackpadY, 'right', 'down-up')

    def edit_mode(self, left_ctr, right_ctr, hmd):
        pass