import sys

import openvr
import time
import os

from steam_vr_wheel.configurator import ConfiguratorApp
from steam_vr_wheel.pyvjoy.vjoydevice import VJoyDevice, \
    HID_USAGE_SL0, HID_USAGE_SL1, HID_USAGE_X, HID_USAGE_Y, HID_USAGE_Z, HID_USAGE_RX, HID_USAGE_RY
from steam_vr_wheel.vrcontroller import Controller
from steam_vr_wheel.util import dead_and_stretch, expand_to_array
from . import PadConfig, ConfigException, MEDIA_DIR, IMAGE_DATA
from . import check_result, rotation_matrix, deep_get
import multiprocessing

BUTTONS = {
    'left': {
        #openvr.k_EButton_Grip: 2,
        openvr.k_EButton_A: 17,
        openvr.k_EButton_ApplicationMenu: 3,

        openvr.k_EButton_SteamVR_Touchpad: [4, 5, 6, 7, 8],
        'left-right': [34, 35],
        'down-up': [36, 37],
        
        openvr.k_EButton_SteamVR_Trigger: 1,
        'trigger-touch': 31,
    },
    'right': {
        #openvr.k_EButton_Grip: 10,
        openvr.k_EButton_A: 18,
        openvr.k_EButton_ApplicationMenu: 11,

        openvr.k_EButton_SteamVR_Touchpad: [12, 13, 14, 15, 16],
        'left-right': [38, 39],
        'down-up': [40, 41],

        openvr.k_EButton_SteamVR_Trigger: 9,
        'trigger-touch': 32,
    }
}

AXES = {
    'left': {
        'left-right': HID_USAGE_Z,
        'down-up': HID_USAGE_Y,
        openvr.k_EButton_SteamVR_Trigger: HID_USAGE_SL0
    },
    'right': {
        'left-right': HID_USAGE_RX,
        'down-up': HID_USAGE_RY,
        openvr.k_EButton_SteamVR_Trigger: HID_USAGE_SL1
    }
}

DISABLED_BUTTONS = set()
DISABLED_AXES = set()

def run_configurator():
    ConfiguratorApp().run()


class HandsImage:
    def __init__(self, left_ctr, right_ctr):
        self._handl_closed = False
        self._handr_closed = False
        self.left_ctr = left_ctr
        self.right_ctr = right_ctr
        hand_size = 0.14
        self.alpha = 0.9
        self.hand_z_offset = 0.03

        self.vrsys = openvr.VRSystem()
        self.vroverlay = openvr.IVROverlay()

        result, self.l_ovr = self.vroverlay.createOverlay('left_hand'.encode(), 'left_hand'.encode())
        result, self.l_ovr2 = self.vroverlay.createOverlay('left_hand_closed'.encode(), 'left_hand_closed'.encode()) #!!
        result, self.r_ovr = self.vroverlay.createOverlay('right_hand'.encode(), 'right_hand'.encode())
        result, self.r_ovr2 = self.vroverlay.createOverlay('right_hand_closed'.encode(), 'right_hand_closed'.encode()) #!!

        check_result(self.vroverlay.setOverlayColor(self.l_ovr, 1, 1, 1))
        check_result(self.vroverlay.setOverlayColor(self.l_ovr2, 1, 1, 1))
        check_result(self.vroverlay.setOverlayColor(self.r_ovr, 1, 1, 1))
        check_result(self.vroverlay.setOverlayColor(self.r_ovr2, 1, 1, 1))
        check_result(self.vroverlay.setOverlayAlpha(self.l_ovr, self.alpha))
        check_result(self.vroverlay.setOverlayAlpha(self.l_ovr2, 0))
        check_result(self.vroverlay.setOverlayAlpha(self.r_ovr, self.alpha))
        check_result(self.vroverlay.setOverlayAlpha(self.r_ovr2, 0))
        check_result(self.vroverlay.setOverlayWidthInMeters(self.l_ovr, hand_size))
        check_result(self.vroverlay.setOverlayWidthInMeters(self.l_ovr2, hand_size))
        check_result(self.vroverlay.setOverlayWidthInMeters(self.r_ovr, hand_size))
        check_result(self.vroverlay.setOverlayWidthInMeters(self.r_ovr2, hand_size))
        check_result(self.vroverlay.setOverlaySortOrder(self.l_ovr, 0))
        check_result(self.vroverlay.setOverlaySortOrder(self.l_ovr2, 0))
        check_result(self.vroverlay.setOverlaySortOrder(self.r_ovr, 0))
        check_result(self.vroverlay.setOverlaySortOrder(self.r_ovr2, 0))

        #this_dir = os.path.abspath(os.path.dirname(__file__))

        self.l_open_png = os.path.join(MEDIA_DIR, 'hand_open_l.png')
        self.r_open_png = os.path.join(MEDIA_DIR, 'hand_open_r.png')
        self.l_close_png = os.path.join(MEDIA_DIR, 'hand_closed_l.png')
        self.r_close_png = os.path.join(MEDIA_DIR, 'hand_closed_r.png')

        check_result(self.vroverlay.setOverlayRaw(self.l_ovr, *IMAGE_DATA[self.l_open_png]))
        check_result(self.vroverlay.setOverlayRaw(self.l_ovr2, *IMAGE_DATA[self.l_close_png]))
        check_result(self.vroverlay.setOverlayRaw(self.r_ovr, *IMAGE_DATA[self.r_open_png]))
        check_result(self.vroverlay.setOverlayRaw(self.r_ovr2, *IMAGE_DATA[self.r_close_png]))

        result, ctr_tf = self.vroverlay.setOverlayTransformTrackedDeviceRelative(self.l_ovr, self.left_ctr.id)
        result, ctr_tf = self.vroverlay.setOverlayTransformTrackedDeviceRelative(self.l_ovr2, self.left_ctr.id)
        result, ctr_tf = self.vroverlay.setOverlayTransformTrackedDeviceRelative(self.r_ovr, self.right_ctr.id)
        result, ctr_tf = self.vroverlay.setOverlayTransformTrackedDeviceRelative(self.r_ovr2, self.right_ctr.id)

        ctr_tf[0][0] = 1.0
        ctr_tf[0][1] = 0.0
        ctr_tf[0][2] = 0.0
        ctr_tf[0][3] = 0

        ctr_tf[1][0] = 0.0
        ctr_tf[1][1] = 0.0
        ctr_tf[1][2] = 1.0
        ctr_tf[1][3] = 0

        ctr_tf[2][0] = 0.0
        ctr_tf[2][1] = -1.0
        ctr_tf[2][2] = 0.0
        ctr_tf[2][3] = self.hand_z_offset

        self.ctr_tf = ctr_tf
        self.attach_to_ctr('left')
        self.attach_to_ctr('right')

        check_result(result)
        check_result(self.vroverlay.showOverlay(self.l_ovr))
        check_result(self.vroverlay.showOverlay(self.l_ovr2))
        check_result(self.vroverlay.showOverlay(self.r_ovr))
        check_result(self.vroverlay.showOverlay(self.r_ovr2))

    def closed_hands_always_top(self):
        check_result(self.vroverlay.setOverlaySortOrder(self.l_ovr2, 1))
        check_result(self.vroverlay.setOverlaySortOrder(self.r_ovr2, 1))

    def move(self, hand, tf):
        fn = self.vroverlay.function_table.setOverlayTransformAbsolute
        if hand == 'left':
            check_result(fn(self.l_ovr, openvr.TrackingUniverseSeated, openvr.byref(tf)))
            check_result(fn(self.l_ovr2, openvr.TrackingUniverseSeated, openvr.byref(tf)))
        elif hand == 'right':
            check_result(fn(self.r_ovr, openvr.TrackingUniverseSeated, openvr.byref(tf)))
            check_result(fn(self.r_ovr2, openvr.TrackingUniverseSeated, openvr.byref(tf)))

    def attach_to_ctr(self, hand):
        fn = self.vroverlay.function_table.setOverlayTransformTrackedDeviceRelative
        if hand == 'left':
            check_result(fn(self.l_ovr, self.left_ctr.id, openvr.byref(self.ctr_tf)))
            check_result(fn(self.l_ovr2, self.left_ctr.id, openvr.byref(self.ctr_tf)))
        elif hand == 'right':
            check_result(fn(self.r_ovr, self.right_ctr.id, openvr.byref(self.ctr_tf)))
            check_result(fn(self.r_ovr2, self.right_ctr.id, openvr.byref(self.ctr_tf)))

    def left_grab(self):
        if not self._handl_closed:
            #self.vroverlay.setOverlayFromFile(self.l_ovr, self.l_close_png.encode())
            self.vroverlay.setOverlayAlpha(self.l_ovr, 0)
            self.vroverlay.setOverlayAlpha(self.l_ovr2, self.alpha)
            self._handl_closed = True

    def left_ungrab(self):
        if self._handl_closed:
            #self.vroverlay.setOverlayFromFile(self.l_ovr, self.l_open_png.encode())
            self.vroverlay.setOverlayAlpha(self.l_ovr, self.alpha)
            self.vroverlay.setOverlayAlpha(self.l_ovr2, 0)
            self._handl_closed = False

    def right_grab(self):
        if not self._handr_closed:
            #self.vroverlay.setOverlayFromFile(self.r_ovr, self.r_close_png.encode())
            self.vroverlay.setOverlayAlpha(self.r_ovr, 0)
            self.vroverlay.setOverlayAlpha(self.r_ovr2, self.alpha)
            self._handr_closed = True

    def right_ungrab(self):
        if self._handr_closed:
            #self.vroverlay.setOverlayFromFile(self.r_ovr, self.r_open_png.encode())
            self.vroverlay.setOverlayAlpha(self.r_ovr, self.alpha)
            self.vroverlay.setOverlayAlpha(self.r_ovr2, 0)
            self._handr_closed = False

    def hide(self):
        check_result(self.vroverlay.hideOverlay(self.l_ovr))
        check_result(self.vroverlay.hideOverlay(self.l_ovr2))
        check_result(self.vroverlay.hideOverlay(self.r_ovr))
        check_result(self.vroverlay.hideOverlay(self.r_ovr2))

    def show(self):
        check_result(self.vroverlay.showOverlay(self.l_ovr))
        check_result(self.vroverlay.showOverlay(self.l_ovr2))
        check_result(self.vroverlay.showOverlay(self.r_ovr))
        check_result(self.vroverlay.showOverlay(self.r_ovr2))

    def set_color(self, cl):
        check_result(self.vroverlay.setOverlayColor(self.l_ovr, *cl))
        check_result(self.vroverlay.setOverlayColor(self.l_ovr2, *cl))
        check_result(self.vroverlay.setOverlayColor(self.r_ovr, *cl))
        check_result(self.vroverlay.setOverlayColor(self.r_ovr2, *cl))



class VirtualPad:

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

        self._previous_update_time = time.time()

        # for triple grip:
        self._grip_times = dict({'left': [], 'right': []})

        # Haptic intensity
        Controller.set_haptic_intensity(self.config.haptic_intensity / 100)

        # edit mode
        self._edit_mode_last_press = 0.0
        self._edit_mode_entry = 0.0

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

    def set_button(self, btn_id, val):
        if btn_id in DISABLED_BUTTONS:
            return
        self.device.set_button(btn_id, val)

    def set_axis(self, axis_id, val):
        if axis_id in DISABLED_AXES:
            return
        self.device.set_axis(axis_id, val)

    def enable_all(self):
        DISABLED_BUTTONS.clear()
        DISABLED_AXES.clear()

    def enable_button(self, hand, button):
        btn_id = BUTTONS[hand][button]
        DISABLED_BUTTONS.remove(btn_id)

    def disable_button(self, hand, button):
        btn_id = BUTTONS[hand][button]
        DISABLED_BUTTONS.add(btn_id)
        self.device.set_button(btn_id, False)

    def enable_axis(self, hand, axis):
        axis_id = AXES[hand][axis]
        DISABLED_AXES.remove(axis_id)

        btn_ids = deep_get(BUTTONS, [hand, axis])
        if btn_ids is not None:
            btn_ids = expand_to_array(btn_ids)
            for e in btn_ids:
                DISABLED_BUTTONS.remove(e)

    def get_axis_zero(self, hand, axis):
        is_btns = deep_get(self.axis_buttons, [hand, axis])
        if is_btns is not None:
            return 0.0 if is_btns[0] or is_btns[1] else 0.5
        return 0.0

    def disable_axis(self, hand, axis):
        axis_id = AXES[hand][axis]
        DISABLED_AXES.add(axis_id)
        zero = self.get_axis_zero(hand, axis)
        self.device.set_axis(axis_id, int(zero * 0x8000))

        btn_ids = deep_get(BUTTONS, [hand, axis])
        if btn_ids is not None:
            btn_ids = expand_to_array(btn_ids)
            for e in btn_ids:
                DISABLED_BUTTONS.add(e)

    def update_axis_buttons(self):
        self.axis_buttons = {}
        self.axis_buttons['left'] = {
            'left-right': [
                self.config.j_l_left_button,
                self.config.j_l_right_button
            ],
            'down-up': [
                self.config.j_l_down_button,
                self.config.j_l_up_button
            ]
        }
        self.axis_buttons['right'] = {
            'left-right': [
                self.config.j_r_left_button,
                self.config.j_r_right_button
            ],
            'down-up': [
                self.config.j_r_down_button, 
                self.config.j_r_up_button
            ]
        }

    def get_trackpad_zone(self, X, Y):
        if self.config.multibutton_trackpad:
            zone = self._get_zone(X, Y)
        else:
            zone = 0
        return zone

    def _get_zone(self, x, y):
        if (x**2 + y**2)**0.5 < 0.3: # TODO can this (0.3) be replaced with axis_deadzone?
            return 0
        if x>y:
            if y>(-x):
                return 2 # Right +x
            else:
                return 3 # Down -y
        if x<y:
            if y<(-x):
                return 1 # Left -x
            else:
                return 4 # Up +y

    def pressed_left_trackpad(self):
        zone = self.get_trackpad_zone(self.trackpadLX, self.trackpadLY)
        btn_id = BUTTONS['left'][openvr.k_EButton_SteamVR_Touchpad][zone]
        self.set_button(btn_id, True)

    def unpressed_left_trackpad(self):
        for btn_id in BUTTONS['left'][openvr.k_EButton_SteamVR_Touchpad]:
            try:
                self.set_button(btn_id, False)
            except NameError:
                pass

    def pressed_right_trackpad(self):
        zone = self.get_trackpad_zone(self.trackpadRX, self.trackpadRY)
        btn_id = BUTTONS['right'][openvr.k_EButton_SteamVR_Touchpad][zone]
        self.set_button(btn_id, True)

    def unpressed_right_trackpad(self):
        for btn_id in BUTTONS['right'][openvr.k_EButton_SteamVR_Touchpad]:
            try:
                self.set_button(btn_id, False)
            except NameError:
                pass

    def pre_edit_mode(self):
        pass

    def post_edit_mode(self):
        pass

    def edit_mode(self, frames):
        pass

    def update_chaperone(self, chp):
        pass

    def set_button_press(self, button, hand, left_ctr, right_ctr):
        if button == openvr.k_EButton_SteamVR_Trigger:
            if not self.config.trigger_press_button:
                return

        if button == openvr.k_EButton_Grip:
            now = time.time()
            other = 'left' if hand == 'right' else 'right'
            self._grip_times[hand].append(now)
            self._grip_times[hand] = self._grip_times[hand][-3:]

            if (len(self._grip_times[hand]) >= 3 and
                len(self._grip_times[other]) >= 3 and
                self._grip_times[hand][-1] - self._grip_times[hand][-3] <= 1.0 and
                self._grip_times[other][-1] - self._grip_times[other][-3] <= 1.0):

                self._grip_times[hand] = []
                self._grip_times[other] = []

                if self.is_edit_mode == False:
                    left_ctr.haptic(*[[None, 1], [0.05, None]]*3)
                    right_ctr.haptic(*[[None, 1], [0.05, None]]*3)

                    self._edit_mode_entry = time.time()
                    self.is_edit_mode = True
                    self.pre_edit_mode()
                    
                else:
                    left_ctr.haptic([None, 1])
                    right_ctr.haptic([None, 1])

                    self.is_edit_mode = False
                    self.post_edit_mode()

                return

        try:
            btn_id = BUTTONS[hand][button]
            if btn_id is None:
                return
            elif button == openvr.k_EButton_SteamVR_Touchpad:
                if hand == 'left':
                    self.pressed_left_trackpad()
                else:
                    self.pressed_right_trackpad()
            else:
                self.set_button(btn_id, True)
                
        except KeyError:
            pass

    def set_button_unpress(self, button, hand):
        try:
            btn_id = BUTTONS[hand][button]
            if btn_id is None:
                return
            elif button == openvr.k_EButton_SteamVR_Touchpad:
                if hand == 'left':
                    self.unpressed_left_trackpad()
                else:
                    self.unpressed_right_trackpad()
            else:
                self.set_button(btn_id, False)
        except KeyError:
            pass

    def set_trigger_touch_left(self):
        if self.config.trigger_pre_press_button:
            self.set_button(BUTTONS['left']['trigger-touch'], True)

    def set_trigger_touch_right(self):
        if self.config.trigger_pre_press_button:
            self.set_button(BUTTONS['right']['trigger-touch'], True)

    def set_trigger_untouch_left(self):
        self.set_button(BUTTONS['left']['trigger-touch'], False)

    def set_trigger_untouch_right(self):
        self.set_button(BUTTONS['right']['trigger-touch'], False)

    def set_trackpad_touch_left(self):
        self.trackpadLtouch = True

    def set_trackpad_touch_right(self):
        self.trackpadRtouch = True

    def set_trackpad_untouch_left(self):
        self.trackpadLtouch = False

    def set_trackpad_untouch_right(self):
        self.trackpadRtouch = False

    def get_update_delta(self):
        return self._update_time_delta

    def update(self, left_ctr: Controller, right_ctr: Controller, hmd: Controller):
        now = time.time()
        self._update_time_delta = now - self._previous_update_time
        self._previous_update_time = now

        self.set_axis(AXES['left'][openvr.k_EButton_SteamVR_Trigger], int(left_ctr.axis * 0x8000))
        self.set_axis(AXES['right'][openvr.k_EButton_SteamVR_Trigger], int(right_ctr.axis * 0x8000))

        self.update_axis_buttons()
        DEADZONE_DPAD = 0.9
        DEADZONE_AXIS = self.config.axis_deadzone / 100

        def zero_axis(hand, axis):
            axis_hid = AXES[hand][axis]
            btn_ids = BUTTONS[hand][axis]
            zero = self.get_axis_zero(hand, axis)
            self.set_button(btn_ids[0], False)
            self.set_button(btn_ids[1], False)
            self.set_axis(axis_hid, int(zero * 0x8000))

        def convert_axis(x, y, hand, x_axis, y_axis):

            '''
            This function allows only one direction of joystick to be registered
            that means no overlapping axes; only x or y will be registered

            NOTE you can use this function separately for 'left-right' and 'down-up' axes
                 ( use it like convert_axis(trackpad, hand, axis) )
                 if you'd like it that way
            '''

            if abs(x) > abs(y):
                zero_axis(hand, y_axis)

                trackpad = x
                axis = x_axis
            else:
                zero_axis(hand, x_axis)

                trackpad = y
                axis = y_axis

            axis_hid = AXES[hand][axis]
            btn_ids = BUTTONS[hand][axis]
            is_btns = self.axis_buttons[hand][axis]
            zero = self.get_axis_zero(hand, axis)

            axis_amount = dead_and_stretch(trackpad, DEADZONE_AXIS)
            if is_btns[0] or is_btns[1]:
                axis_amount = abs(axis_amount)
            else:
                axis_amount = (axis_amount + 1) / 2

            plus_dead = DEADZONE_DPAD if is_btns[1] else DEADZONE_AXIS
            minus_dead = -DEADZONE_DPAD if is_btns[0] else -DEADZONE_AXIS

            if trackpad <= minus_dead:

                self.set_button(btn_ids[1], False)
                if is_btns[0]:
                    self.set_button(btn_ids[0], True)
                else:
                    self.set_axis(axis_hid, int(axis_amount * 0x8000))

            elif trackpad >= plus_dead:

                self.set_button(btn_ids[0], False)
                if is_btns[1]:
                    self.set_button(btn_ids[1], True)
                else:
                    self.set_axis(axis_hid, int(axis_amount * 0x8000))

            else:
                zero_axis(hand, axis)

        self.trackpadLX = left_ctr.trackpadX
        self.trackpadLY = left_ctr.trackpadY

        convert_axis(left_ctr.trackpadX, left_ctr.trackpadY, 'left', 'left-right', 'down-up')

        self.trackpadRX = right_ctr.trackpadX
        self.trackpadRY = right_ctr.trackpadY

        convert_axis(right_ctr.trackpadX, right_ctr.trackpadY, 'right', 'left-right', 'down-up')
