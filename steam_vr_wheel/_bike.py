

from math import pi, atan2, sin, cos, ceil, sqrt, acos, tan, asin

import numpy as np
import openvr
import os
import time
import threading
import queue

from . import check_result, rotation_matrix, bezier_curve
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

    def move_rotate(self, pos=None, size=None, pitch_yaw_roll=None):
        if pos is not None:
            self.transform[0][3] = pos[0]
            self.transform[1][3] = pos[1]
            self.transform[2][3] = pos[2]

        if pitch_yaw_roll is not None:
            r = rotation_matrix(-pitch_yaw_roll[0], -pitch_yaw_roll[1], pitch_yaw_roll[2])
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
        # 1800x735
        self.handlebar_image = HandlebarImage(x, y, z, size)
        self.center = np.array([x, y, z])
        self.size = size
        self.size_height = size / 1800 * 735

        self.base_pitch = 20
        self._reset_handlebar()
        self.handlebar_image.move_rotate(pitch_yaw_roll=[self.pitch, self.yaw, 0])
        self.lean = 0
        self.roll_lean = 0
        self.steer = 0
        self.dampered_lean = 0
        self.dampered_roll_lean = 0
        self.dampered_steer = 0

        self.max_steer = self.config.bike_max_steer
        self.max_lean = self.config.bike_max_lean
        self.angle_deadzone = self.config.bike_angle_deadzone
        self.handlebar_height = self.config.bike_handlebar_height / 100.0
        self.handlebar_hand_offset = size/2 - 0.19 # offset of hand from the center; where the hand is placed on
        self._handlebar_r = sqrt(self.handlebar_height**2 + self.handlebar_hand_offset**2)
        self._handlebar_a = atan2(self.handlebar_height, self.handlebar_hand_offset)

        #
        modestr = self.config.bike_mode
        if modestr == "Absolute":
            bound = self.config.bike_bound_hand
            if bound == "Left":
                self.mode = self.BIKE_MODE_ABSOLUTE_LEFT_BOUND
            elif bound == "Right":
                self.mode = self.BIKE_MODE_ABSOLUTE_RIGHT_BOUND
            else:
                self.mode = self.BIKE_MODE_ABSOLUTE
        elif modestr == "Relative":
            self.mode = self.BIKE_MODE_RELATIVE

        #
        self.grabbed = dict({"left": False, "right": False})
        self.run_alway_grab = False

        # Throttle
        self.last_throttle_pitch = None
        self.throttle_grip_threshold = 0.95
        self.throttle = 0.0
        self.throttle_sensitivity = self.config.bike_throttle_sensitivity / 100.0
        self.throttle_decrease_per_second = self.config.bike_throttle_decrease_per_sec / 100.0
        self.throttle_last_haptic = 0

        #
        self.relative_sensitivity = self.config.bike_relative_sensitivity / 100.0

        # edit mode
        self._edit_mode_last_press = 0.0
        self._edit_mode_entry = 0.0


    BIKE_MODE_ABSOLUTE = 1              # Both the hands affect the lean
    BIKE_MODE_ABSOLUTE_LEFT_BOUND = 2   # Only the left hand affects the lean
    BIKE_MODE_ABSOLUTE_RIGHT_BOUND = 3  # only the right

    BIKE_MODE_RELATIVE = 4              # the height difference of left and right hand determines the lean
                                        # the handlebar overlay always stays aligned center to hmd

    def _evaluate_lean_angle(self, left_ctr, right_ctr):

        dx = left_ctr.x - right_ctr.x
        dy = left_ctr.y - right_ctr.y
        dz = left_ctr.z - right_ctr.z

        #
        if self.mode == self.BIKE_MODE_RELATIVE:
            dy *= self.relative_sensitivity
            dz *= self.relative_sensitivity

        # Steer
        steer = 0
        if self.mode in [self.BIKE_MODE_ABSOLUTE, self.BIKE_MODE_RELATIVE]:
            
            if dz > 0:
                dz = max(0, dz - abs(dy))
            else:
                dz = min(0, dz + abs(dy))

            steer = atan2(dz, dx)
            steer *= -1
            steer = (pi if steer > 0 else -pi) - steer

        # Lean
        if self.mode != self.BIKE_MODE_RELATIVE: # TODO fix
            if False and self.grabbed['left'] and self.grabbed['right']:

                x_center = (right_ctr.x - left_ctr.x)/2 + left_ctr.x - self.center[0]
                lean = asin(min(1, max(-1, x_center / self.handlebar_height)))

                # Mix with relative position about the center
                x_max = self.handlebar_height*sin(self.max_lean/180*pi)
                x_percent = abs(x_center/x_max)

                relative_lean = atan2(dy, dx)
                relative_lean = (pi if relative_lean > 0 else -pi) - relative_lean

                lean += relative_lean * (1-x_percent) * 1.0 # TODO config relative angle percentage

            elif self.grabbed['left']:
                # based on left hand's location
                x_hand = left_ctr.x - self.center[0]

                x_max = self.handlebar_height * sin(self.max_lean/180*pi)
                x_middle = x_hand + self.handlebar_hand_offset

                lean = acos(min(1, max(-1, x_hand / self._handlebar_r))) + self._handlebar_a
                lean -= pi
                lean *= -1

                steer = atan2(left_ctr.z - self.center[2], -self.handlebar_hand_offset)
                steer *= -1
                steer = (pi if steer > 0 else -pi) - steer

            elif False and self.grabbed['right']:
                # based on right hand's location
                x_hand = right_ctr.x - self.center[0]
                lean = acos(min(1, max(-1, x_hand / self._handlebar_r))) - self._handlebar_a
                lean *= -1

                steer = 0

            else:

                return

        elif self.mode == self.BIKE_MODE_RELATIVE:

            lean = atan2(dy, dx)
            lean = (pi if lean > 0 else -pi) - lean

        #
        steer = steer/pi*180
        steer = min(max(steer, -self.max_steer), self.max_steer)

        lean = lean/pi*180
        roll_lean = lean

        # Less steer effect at high lean
        steer *= max(0, (self.max_steer-abs(lean))/self.max_steer)
        lean += steer

        # Clamp
        lean = min(max(lean, -self.max_lean), self.max_lean)

        # Deadzone
        lower = self.max_lean * (self.angle_deadzone / 100.0)
        if abs(lean) < lower:
            lean = 0
        else:
            if lean > 0:
                lean -= lower
            else:
                lean += lower

            lean *= 100/(100-self.angle_deadzone)

        #
        self.lean = lean
        self.roll_lean = roll_lean
        self.steer = steer

        #
        self.central_stablize()
        self.damper()

        # right hand
        # sin(lean) * hh + cos(lean) * o = x
        # left hand
        # sin(lean) * hh - cos(lean) * o = x

    def central_stablize(self):
        stablizer_curve = [np.array([0, 0]),
                            np.array([0.75, 0]),
                            np.array([0.25, 0.9]),
                            np.array([1, 1])]
        s = 1
        if self.lean < 0:
            s = -1
        self.lean = bezier_curve(abs(self.lean)/self.max_lean,
            *stablizer_curve)[1] * self.max_lean * s
        self.roll_lean = bezier_curve(abs(self.roll_lean)/self.max_lean,
            *stablizer_curve)[1] * self.max_lean * s
        
    def damper(self):
        DAMPER = 10 / (60 * self.get_update_delta())
        DAMPER = max(1, DAMPER)
        self.dampered_lean += (self.lean - self.dampered_lean) / DAMPER # TODO config dampering factor
        self.dampered_roll_lean += (self.roll_lean - self.dampered_roll_lean) / DAMPER
        self.dampered_steer += (self.steer - self.dampered_steer) / DAMPER
        
        self.pitch = self.base_pitch + abs(self.dampered_lean)

        if self.mode == self.BIKE_MODE_RELATIVE:
            self.yaw = self.dampered_roll_lean / 2
        else:
            self.yaw = self.dampered_steer + self.dampered_lean

        self.x_offset = self.handlebar_height*sin(self.dampered_roll_lean/180*pi)
        self.y_offset = self.handlebar_height*cos(self.dampered_roll_lean/180*pi) - self.handlebar_height
        self.z_offset = -1 * (cos(self.dampered_roll_lean /180*pi) - 1)

    def render(self, hmd):

        if self.mode == self.BIKE_MODE_RELATIVE:
            self.handlebar_image.move_rotate(
                pos=[hmd.x+self.center[0],
                    hmd.y+self.center[1],
                    hmd.z+self.center[2]],
                pitch_yaw_roll=[self.pitch, self.yaw, -self.dampered_roll_lean])

            """
            vrchp_setup = openvr.VRChaperoneSetup()
            chp = openvr.HmdMatrix34_t()
            for i in range(3):
                for j in range(4):
                    chp[i][j] = self.original_chaperone[i][j]
            chp[0][3] = chp[0][3] - self.x_offset - (hmd.x + self.current_chaperone[0][3])
            #print((hmd.x + self.current_chaperone[0][3]))
            self.current_chaperone = chp
            vrchp_setup.function_table.setWorkingSeatedZeroPoseToRawTrackingPose(openvr.byref(chp))
            vrchp_setup.commitWorkingCopy(openvr.EChaperoneConfigFile_Live)
            """

        else:
            self.handlebar_image.move_rotate(
                pos=[self.center[0]+self.x_offset,
                    self.center[1]+self.y_offset,
                    self.center[2]+self.z_offset],
                pitch_yaw_roll=[self.pitch, self.yaw, -self.dampered_roll_lean])

        if self.config.bike_show_hands:
            self.hands_overlay.show()
        else:
            self.hands_overlay.hide()

        if self.config.bike_show_handlebar:
            self.handlebar_image.show()
        else:
            self.handlebar_image.hide()

    def _update_throttle(self, right_ctr):

        now = time.time()

        if self.last_throttle_pitch and right_ctr.axis2 >= self.throttle_grip_threshold:
            diff = right_ctr.yaw - self.last_throttle_pitch
            diff = (diff+180) % 360 - 180

            #print(right_ctr.pitch, right_ctr.yaw, right_ctr.roll)

            diff = -(diff / (100.0 / self.throttle_sensitivity))

            if diff > 0:
                pass
            else:
                diff *= 3 # TODO throttle decrease sensitivity

            self.throttle += diff
            self.throttle = min(1.0, max(0.0, self.throttle))

            if now - self.throttle_last_haptic > 0.06:
                if self.throttle > 0.05:
                    amount = bezier_curve(self.throttle,
                        np.array([0, 0]),
                        np.array([0.6, 0]),
                        np.array([0, 1]),
                        np.array([1, 1]))[1] * 5000
                    openvr.VRSystem().triggerHapticPulse(right_ctr.id, 0, int(amount))
                self.throttle_last_haptic = now

            self.last_throttle_pitch = right_ctr.yaw

        elif self.throttle > 0.0:
            self.throttle -= self.get_update_delta() * self.throttle_decrease_per_second
            self.throttle = max(0.0, self.throttle)

        self.device.set_axis(HID_USAGE_RZ, int(self.throttle * 0x8000))

    def update_chaperone(self, chp):
        self.original_chaperone = chp
        self.current_chaperone = chp

    def update_grip(self, hand, ctr):

        grabber = self.hands_overlay.left_grab if hand == 'left' else self.hands_overlay.right_grab
        ungrabber = self.hands_overlay.left_ungrab if hand == 'left' else self.hands_overlay.right_ungrab

        if hand == 'left': # TEST
            self.grabbed[hand] = True
            grabber()

        if ctr.axis2 > 0:
            if hand == 'right' and self.grabbed['right'] == False:
                self.last_throttle_pitch = ctr.yaw

            self.grabbed[hand] = True
            grabber()
        else:
            self.grabbed[hand] = False
            ungrabber()

    def update(self, left_ctr, right_ctr, hmd):
        super().update(left_ctr, right_ctr, hmd)

        # Update grip
        self.update_grip('left', left_ctr)
        self.update_grip('right', right_ctr)

        # Update lean
        self._evaluate_lean_angle(left_ctr, right_ctr)

        # Throttle
        self._update_throttle(right_ctr)

        # vJoy
        axisX = int(((self.dampered_lean/self.max_lean)+1)/2.0 * 0x8000)
        self.device.set_axis(HID_USAGE_X, axisX)

        self.render(hmd)

    def move_delta(self, d):
        self.center = np.array([0, self.center[1] + d[1], self.center[2] + d[2]])
        #self.config.bike_center = self.center.copy()
        self.handlebar_image.move_rotate(pos=self.center, size=self.size)

    def _reset_handlebar(self):
        self.pitch = self.base_pitch
        self.yaw = 0
        self.lean = 0
        self.x_offset = 0
        self.y_offset = 0
        self.z_offset = 0

    def pre_edit_mode(self):
        super().pre_edit_mode()

        self._reset_handlebar()

    def edit_mode(self, left_ctr, right_ctr, hmd):
        super().edit_mode(left_ctr, right_ctr, hmd)

        now = time.time()

        if hasattr(self, "_edit_check") == False:
            self._edit_check = True
            self._edit_move_handlebar = False
            self._edit_last_l_pos = [left_ctr.x, left_ctr.y, left_ctr.z]
            self._edit_last_r_pos = [right_ctr.x, right_ctr.y, right_ctr.z]

            self.handlebar_image.set_alpha(1)

        if (left_ctr.is_pressed(openvr.k_EButton_Grip) or right_ctr.is_pressed(openvr.k_EButton_Grip)) and now - self._edit_mode_entry > 0.5:
            self.handlebar_image.set_color([1, 1, 1])
            self.is_edit_mode = False
            self.__dict__.pop("_edit_check", None)
            return

        mover = None
        if left_ctr.is_pressed(openvr.k_EButton_SteamVR_Trigger):
            mover = left_ctr
        if right_ctr.is_pressed(openvr.k_EButton_SteamVR_Trigger):
            mover = right_ctr

        self._edit_move_handlebar = mover is not None
        if self._edit_move_handlebar:
            self.handlebar_image.set_color([1, 0, 0])

            #
            r_d = [right_ctr.x-self._edit_last_r_pos[0], right_ctr.y-self._edit_last_r_pos[1], right_ctr.z-self._edit_last_r_pos[2]]
            self.move_delta(r_d)

        else:
            self.handlebar_image.set_color([0, 1, 0])

        self.render(hmd)

        #
        self._edit_last_l_pos = [left_ctr.x, left_ctr.y, left_ctr.z]
        self._edit_last_r_pos = [right_ctr.x, right_ctr.y, right_ctr.z]
