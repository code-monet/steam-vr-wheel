

import numpy as np
import openvr
import os
import time
import threading
import queue

from steam_vr_wheel._virtualpad import VirtualPad
from steam_vr_wheel.pyvjoy.vjoydevice import VJoyDevice, HID_USAGE_RZ

# IVRChaperoneSetup

# Memo for references
# https://github.com/OpenVR-Advanced-Settings/OpenVR-AdvancedSettings/blob/72e91e91165fff97df09c0a24464bc9856fe387c/src/tabcontrollers/MoveCenterTabController.cpp#L2509
# https://www.youtube.com/watch?v=cS3DTWq0QV8


def check_result(result):
    if result:
        error_name = openvr.VROverlay().getOverlayErrorNameFromEnum(result)
        raise Exception("OpenVR Error:", error_name)


class HandlebarImage():
    def __init__(self, x=0, y=-0.4, z=-0.35, size=0.50, alpha=1):
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
            self.transform[0][3] = pos.x
            self.transform[1][3] = pos.y
            self.transform[2][3] = pos.z

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
        size = 50 / 100#self.config.bike_handlebar_size
        self.handlebar_image = HandlebarImage(x, y, z, size)
        self.center = np.array([x, y, z])
        self.size = size

        # edit mode
        self._edit_mode_last_press = 0.0
        self._edit_mode_entry = 0.0


