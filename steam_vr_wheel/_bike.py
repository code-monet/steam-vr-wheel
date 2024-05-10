

from math import pi, atan2, sin, cos, ceil, sqrt, acos, tan, asin

import numpy as np
import openvr
import os
import time
import threading
import queue

from . import check_result, rotation_matrix
from steam_vr_wheel._virtualpad import VirtualPad
from steam_vr_wheel.pyvjoy.vjoydevice import HID_USAGE_RZ, HID_USAGE_X

# IVRChaperoneSetup

# Memo for references
# https://github.com/OpenVR-Advanced-Settings/OpenVR-AdvancedSettings/blob/72e91e91165fff97df09c0a24464bc9856fe387c/src/tabcontrollers/MoveCenterTabController.cpp#L2509
# https://www.youtube.com/watch?v=cS3DTWq0QV8


class HandlebarImage():
    def __init__(self, x=0, y=-0.4, z=-0.35, size=0.80, alpha=1):
        self.vrsys = openvr.VRSystem()
        self.vroverlay = openvr.IVROverlay()
        result, self.handlebar = self.vroverlay.createOverlay('handlebar'.encode(), 'handlebar'.encode())
        check_result(result)

        check_result(self.vroverlay.setOverlayColor(self.handlebar, 1, 1, 1))
        check_result(self.vroverlay.setOverlayAlpha(self.handlebar, alpha))
        check_result(self.vroverlay.setOverlayWidthInMeters(self.handlebar, size))

        this_dir = os.path.abspath(os.path.dirname(__file__))
        handlebar_img = os.path.join(this_dir, 'media', 'handlebar.png')

        check_result(self.vroverlay.setOverlayFromFile(self.handlebar, handlebar_img.encode()))

        result, transform = self.vroverlay.setOverlayTransformAbsolute(self.handlebar, openvr.TrackingUniverseSeated)

        transform[0][0] = 1.0
        transform[0][1] = 0.0
        transform[0][2] = 0.0
        transform[0][3] = x

        transform[1][0] = 0.0
        transform[1][1] = 1.0
        transform[1][2] = 0.0
        transform[1][3] = y

        transform[2][0] = 0.0
        transform[2][1] = 0.0
        transform[2][2] = 1.0
        transform[2][3] = z

        self.transform = transform
        self.size = size

        fn = self.vroverlay.function_table.setOverlayTransformAbsolute
        pmatTrackingOriginToOverlayTransform = transform
        result = fn(self.handlebar, openvr.TrackingUniverseSeated, openvr.byref(pmatTrackingOriginToOverlayTransform))

        check_result(result)
        check_result(self.vroverlay.showOverlay(self.handlebar))

    def set_color(self, cl):
        check_result(self.vroverlay.setOverlayColor(self.handlebar, *cl))

    def set_alpha(self, alpha):
        check_result(self.vroverlay.setOverlayAlpha(self.handlebar, alpha))

    def move_rotate(self, pos=None, size=None, pitch_roll=None):
        if pos is not None:
            self.transform[0][3] = pos[0]
            self.transform[1][3] = pos[1]
            self.transform[2][3] = pos[2]

        if pitch_roll is not None:
            r = rotation_matrix(-pitch_roll[0], 0, pitch_roll[1])
            for i in range(3):
                for j in range(3):
                    self.transform[i][j] = r[i,j]

        fn = self.vroverlay.function_table.setOverlayTransformAbsolute
        fn(self.handlebar, openvr.TrackingUniverseSeated, openvr.byref(self.transform))

        if size is not None:
            self.size = size
            check_result(self.vroverlay.setOverlayWidthInMeters(self.handlebar, size))

    def hide(self):
        check_result(self.vroverlay.hideOverlay(self.handlebar))

    def show(self):
        check_result(self.vroverlay.showOverlay(self.handlebar))



class Bike(VirtualPad):
    def __init__(self):
        super().__init__()
        self.vrsys = openvr.VRSystem()
        self.hands_overlay = None
        self.is_edit_mode = False

        x, y, z = [0, -0.4, -0.35]#self.config.bike_handlebar_center
        size = 80 / 100#self.config.bike_handlebar_size
        self.handlebar_image = HandlebarImage(x, y, z, size)
        self.center = np.array([x, y, z])
        self.size = size

        self.pitch = 20
        self.lean = 0
        self.x_offset = 0
        self.handlebar_image.move_rotate(pitch_roll=[self.pitch, 0])

        self.max_lean = self.config.bike_max_lean
        self.handlebar_height = self.config.bike_handlebar_height / 100.0
        self.handlebar_hand_offset = size/2 - 0.15 # offset of hand from the center; where the hand is placed on
        self._handlebar_r = sqrt(self.handlebar_height**2 + self.handlebar_hand_offset**2)
        self._handlebar_a = atan2(self.handlebar_height, self.handlebar_hand_offset)

        #
        self.grabbed = dict({"left": False, "right": False})

        # edit mode
        self._edit_mode_last_press = 0.0
        self._edit_mode_entry = 0.0

    def set_button_unpress(self, button, hand):
        super().set_button_unpress(button, hand)

        #if self.config.bike_grabbed_by_grip_toggle:
        if button == openvr.k_EButton_Grip:
            self.grabbed[hand] = False
            ungrabber = self.hands_overlay.left_ungrab if hand == 'left' else self.hands_overlay.right_ungrab
            ungrabber()

        #else:
        #    pass

    def set_button_press(self, button, hand, left_ctr, right_ctr):
        ctr = left_ctr if hand == 'left' else right_ctr
        super().set_button_press(button, hand)

        if button == openvr.k_EButton_Grip:
            #if self.config.wheel_grabbed_by_grip_toggle:
            self.grabbed[hand] = True
            grabber = self.hands_overlay.left_grab if hand == 'left' else self.hands_overlay.right_grab
            grabber()

    def _evaluate_lean_angle(self, left_ctr, right_ctr):

        if self.grabbed['left'] and self.grabbed['right']:
            x_center = (right_ctr.x - left_ctr.x)/2 + left_ctr.x - self.center[0]
            lean = asin(min(1, max(-1, x_center / self.handlebar_height)))

        elif self.grabbed['left']:
            x_hand = left_ctr.x - self.center[0]
            lean = acos(min(1, max(-1, x_hand / self._handlebar_r))) + self._handlebar_a
            lean -= pi
            lean *= -1

        elif self.grabbed['right']:
            x_hand = right_ctr.x - self.center[0]
            lean = acos(min(1, max(-1, x_hand / self._handlebar_r))) - self._handlebar_a
            lean *= -1

        else:
            return (None, None)

        lean = lean/pi*180
        lean = min(max(lean, -self.max_lean), self.max_lean)
        return (lean, self.handlebar_height*sin(lean/180*pi))

        # right hand
        # sin(lean) * hh + cos(lean) * o = x
        # left hand
        # sin(lean) * hh - cos(lean) * o = x

    def render(self):
        self.handlebar_image.move_rotate(
            pos=[self.center[0]+self.x_offset, self.center[1], self.center[2]],
            pitch_roll=[self.pitch, -self.lean])

    def update(self, left_ctr, right_ctr, hmd):
        super().update(left_ctr, right_ctr, hmd)

        # Update lean
        lean, x_offset = self._evaluate_lean_angle(left_ctr, right_ctr)
        if lean:
            self.lean = lean
            self.x_offset = x_offset

        # vJoy
        axisX = int(((self.lean/self.max_lean)+1)/2.0 * 0x8000)
        self.device.set_axis(HID_USAGE_X, axisX)

        self.render()

