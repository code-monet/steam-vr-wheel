

from math import pi, atan2, sin, cos, ceil, sqrt, acos, tan, asin

import numpy as np
import openvr
import os
import time
import threading
import queue

import socket
import struct

from . import check_result, rotation_matrix, bezier_curve, Point, MEDIA_DIR, IMAGE_DATA
from steam_vr_wheel.wheel import wheel_main_done
from steam_vr_wheel._virtualpad import VirtualPad, HandsImage
from steam_vr_wheel.pyvjoy.vjoydevice import HID_USAGE_RZ, HID_USAGE_X

# IVRChaperoneSetup

# Memo for references
# https://github.com/OpenVR-Advanced-Settings/OpenVR-AdvancedSettings/blob/72e91e91165fff97df09c0a24464bc9856fe387c/src/tabcontrollers/MoveCenterTabController.cpp#L2509
# https://www.youtube.com/watch?v=cS3DTWq0QV8

def ac_telemetry_loop(speed_callback):

    ac_server_ip = '127.0.0.1'  # Replace with the actual IP address of the ACServer
    ac_server_port = 9996

    def decode_utf_16_le(p):
        # 0x2500 = % = end of string
        for i in range(len(p)):
            c = p[i]

            if c == 0 and i > 1 and p[i-1] == 0x25:
                return p[:i-1].decode('utf-16-le').strip('\x00')

        raise Exception("Wrong data given for utf 16 string")
    
    # Create the UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(3)
    sock.connect((ac_server_ip, ac_server_port))

    sock_used = False

    while not wheel_main_done():

        if sock_used:
            sock_used = False

            # Pack the data according to the specified structure
            packet = struct.pack('<3i', identifier, version, 3) # 3 for dismiss
            # Send the packet to the specified IP and port
            sock.send(packet)

            print("Dismissed previous ac telemetry subscription")
        
        ### Handshake 1
        print("Attempt new handshake with AC server")
        # Pack the data according to the specified structure
        packet = struct.pack('<3i', 1, 1, 0)
        # Send the packet to the specified IP and port
        sock.send(packet)
        
        ### Handshake recv 1
        try:
            data, addr = sock.recvfrom(2048)  # Buffer size is 2048 bytes
            unpacked_data = struct.unpack('<100s 100s 2i 100s 100s', data)

            car_name = decode_utf_16_le(unpacked_data[0])
            driver_name = decode_utf_16_le(unpacked_data[1])
            identifier = unpacked_data[2]
            version = unpacked_data[3]
            track_name = decode_utf_16_le(unpacked_data[4])
            track_config = decode_utf_16_le(unpacked_data[5])

            print(car_name, "CAR")

        except socket.timeout:
            continue
        
        except ConnectionResetError:
            time.sleep(6)
            continue

        ### Handshake 2
        # Pack the data according to the specified structure
        packet = struct.pack('<3i', identifier, version, 1) # 1 for Subscription
        # Send the packet to the specified IP and port
        sock.send(packet)

        # https://github.com/rickwest/ac-remote-telemetry-client/blob/master/src/parsers/RTCarInfoParser.js
        format_string = '''<4s i
                        3f 6? 2? 3f 4i
                        5f i f
                        4f 4f 4f 4f 4f 4f 4f 4f 4f 4f
                        4f 4f 4f
                        4f f f 3f'''
        sock_used = True

        while not wheel_main_done():
            try:
                data, addr = sock.recvfrom(2048)  # Buffer size is 2048 bytes
                if len(data) != 328:
                    time.sleep(0.1)
                    continue
                unpacked_data = struct.unpack(format_string, data)

                speed_Kmh = unpacked_data[2]
                speed_callback(speed_Kmh)

            except socket.timeout:
                break

    sock.close()


class AC_Calibration():
    def __init__(self, spd_max_lean=60, spd_max_axis_sensitivity=125, curve_curvature=0.0):
        self.spd_max_lean = spd_max_lean
        self.spd_max_axis_sensitivity = spd_max_axis_sensitivity
        self.curve_curvature = min(max(0.0, curve_curvature), 1.0)

    def to_axis(self, lean_axis, spd):
        y = 0.5 - self.curve_curvature * 0.5
        lean_to_axis_curve = [np.array([0, 0]),
                            np.array([0.5 + min(1.0, spd/self.spd_max_axis_sensitivity)/2, y]),
                            np.array([0.5 + min(1.0, spd/self.spd_max_axis_sensitivity)/2, y]),
                            np.array([1, 1])]

        s = 1
        if lean_axis < 0:
            s = -1
        a = bezier_curve(abs(lean_axis), *lean_to_axis_curve)[1]
        return a * s

    def max_lean_multiplier(self, spd):
        return max(0.1, min(1.0, spd/self.spd_max_lean))

class HandlebarImage():
    def __init__(self, x=0, y=-0.4, z=-0.35, size=0.80, alpha=1):
        self.vrsys = openvr.VRSystem()
        self.vroverlay = openvr.IVROverlay()
        result, self.handlebar = self.vroverlay.createOverlay('handlebar'.encode(), 'handlebar'.encode())
        check_result(result)

        check_result(self.vroverlay.setOverlayColor(self.handlebar, 1, 1, 1))
        check_result(self.vroverlay.setOverlayAlpha(self.handlebar, alpha))
        check_result(self.vroverlay.setOverlayWidthInMeters(self.handlebar, size))

        #this_dir = os.path.abspath(os.path.dirname(__file__))
        handlebar_img = os.path.join(MEDIA_DIR, 'handlebar.png')

        check_result(self.vroverlay.setOverlayRaw(self.handlebar, *IMAGE_DATA[handlebar_img]))

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

    # Calibrated for personal use: bmw_s_1000_rr_by_bodysut_swapped_spec in Assetto corsa
    AC_CAL_BMWS1000RR = AC_Calibration(115, 160, 0.8) # add max lean angle
    ### 115 160
    """
    at 0 - too much lean angle, maybe 5 deg at max

    up to 60 - too sensitive
    60 - balanced sensitivity
    from 60 - gets less sensitive
    """
    
    AC_CAL = AC_CAL_BMWS1000RR

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

        self._last_left_ctr_pos = None
        self._last_right_ctr_pos = None

        self.max_steer = self.config.bike_max_steer
        self.max_lean = self.config.bike_max_lean
        self.angle_deadzone = self.config.bike_angle_deadzone
        self.handlebar_height = self.config.bike_handlebar_height / 100.0
        self.handlebar_hand_offset = size/2 - 0.19 # offset of hand from the center; where the hand is placed on
        self._handlebar_r = sqrt(self.handlebar_height**2 + self.handlebar_hand_offset**2)
        self._handlebar_a = atan2(self.handlebar_height, self.handlebar_hand_offset)

        self.x_center = 0
        self.dx = self.handlebar_hand_offset * 2
        self.dy = 0
        self.dz = 0

        #
        self.grabbed = dict({"left": False, "right": False})
        self.run_alway_grab = False

        # Throttle
        self.throttle_raw_yaws = None
        self.throttle_yaw_dec_threshold = 10
        self.throttle_yaw_inc_threshold = 10
        self.throttle = 0.0
        self.throttle_sensitivity = self.config.bike_throttle_sensitivity / 100.0
        self.throttle_decrease_per_second = self.config.bike_throttle_decrease_per_sec / 100.0

        #
        self.relative_sensitivity = self.config.bike_relative_sensitivity / 100.0

        # edit mode
        self._edit_mode_last_press = 0.0
        self._edit_mode_entry = 0.0

        # Assetto Corsa telemetry
        if self.config.bike_use_ac_server:
            self.ac_speed = self.AC_CAL.spd_max_lean
            def speed_callback(spd):
                self.ac_speed = spd

            thread = threading.Thread(target=ac_telemetry_loop, args=(speed_callback,), daemon=True)
            thread.start()

    def _evaluate_lean_angle(self, left_ctr, right_ctr):

        if self._last_left_ctr_pos is None:
            self._last_left_ctr_pos = Point(left_ctr.x, left_ctr.y, left_ctr.z)
            self._last_right_ctr_pos = Point(right_ctr.x, right_ctr.y, right_ctr.z)

    
        left_dp = Point(left_ctr.x - self._last_left_ctr_pos.x,
                        left_ctr.y - self._last_left_ctr_pos.y,
                        left_ctr.z - self._last_left_ctr_pos.z)
                        
        right_dp = Point(right_ctr.x - self._last_right_ctr_pos.x,
                            right_ctr.y - self._last_right_ctr_pos.y,
                            right_ctr.z - self._last_right_ctr_pos.z)

        self._last_left_ctr_pos = Point(left_ctr.x, left_ctr.y, left_ctr.z)
        self._last_right_ctr_pos = Point(right_ctr.x, right_ctr.y, right_ctr.z)

        # dx = right - left
        if self.grabbed['left'] and self.grabbed['right']:
            self.x_center += (right_dp.x + left_dp.x) / 2
            #self.dy += right_dp.y - left_dp.y
            #self.dz += right_dp.z - left_dp.z

            # Blend
            real_dy = right_ctr.y - left_ctr.y
            real_dz = right_ctr.z - left_ctr.z

            self.dy = 0.95 * self.dy + 0.05 * real_dy
            self.dz = 0.95 * self.dz + 0.05 * real_dz

        elif self.grabbed['left']:
            self.x_center += left_dp.x
            self.dy += -left_dp.y
            self.dz += -left_dp.z

        elif self.grabbed['right']:
            self.x_center += right_dp.x
            self.dy += right_dp.y
            self.dz += right_dp.z

        # 
        x_center = self.x_center
        dx = self.dx
        dy = self.dy
        dz = self.dz

        #
        if False:
            dy *= self.relative_sensitivity
            dz *= self.relative_sensitivity


        # Steer
        steer = 0

        #if False: ####### TEST
        if dz > 0:
            dz = max(0, dz - abs(dy))
        else:
            dz = min(0, dz + abs(dy))

        steer = atan2(dz, dx)

        # Lean
        lean = asin(min(1, max(-1, x_center / self.handlebar_height)))

        #
        steer = steer/pi*180
        steer = min(max(steer, -self.max_steer), self.max_steer)

        lean = lean/pi*180
        roll_lean = lean

        # Clamp
        lean = min(max(lean, -self.max_lean), self.max_lean)
        roll_lean = min(max(roll_lean, -self.max_lean), self.max_lean)

        # Less steer effect at high lean
        steer *= max(0, (self.max_steer-abs(lean))/self.max_steer)
        lean += steer

        #
        self.lean = lean
        self.roll_lean = roll_lean
        self.steer = steer

        #
        self.pitch = self.base_pitch + abs(self.lean)

        if False and self.mode == self.BIKE_MODE_RELATIVE:
            self.yaw = self.roll_lean / 2
        else:
            self.yaw = self.steer + self.lean

        #
        self.x_offset = self.handlebar_height*sin(self.roll_lean/180*pi)
        self.y_offset = self.handlebar_height*cos(self.roll_lean/180*pi) - self.handlebar_height
        self.z_offset = -1 * (cos(self.roll_lean /180*pi) - 1)

        # TODO use hmd x to adjust steering axis; body's center of mass

        #
        #self.central_stablize()
        #self.damper()

        # right hand
        # sin(lean) * hh + cos(lean) * o = x
        # left hand
        # sin(lean) * hh - cos(lean) * o = x

    def render(self, hmd):

        if False and self.mode == self.BIKE_MODE_RELATIVE:
            self.handlebar_image.move_rotate(
                pos=[hmd.x+self.center[0],
                    hmd.y+self.center[1],
                    hmd.z+self.center[2]],
                pitch_yaw_roll=[self.pitch, self.yaw, -self.roll_lean])

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
                pitch_yaw_roll=[self.pitch, self.yaw, -self.roll_lean])

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

        if self.grabbed['right']:

            if self.throttle_raw_yaws is None:
                window_size = 5
                self.throttle_raw_yaws = np.array([right_ctr.yaw]*window_size)
            self.throttle_raw_yaws[1:] = self.throttle_raw_yaws[:-1]
            self.throttle_raw_yaws[0] = right_ctr.yaw
            
            fderivs = np.diff(self.throttle_raw_yaws)
            rms_deriv = np.sqrt(np.mean(np.square(fderivs)))
            
            wrapped_d_yaw = (-(right_ctr.yaw - self.throttle_raw_yaws[1]) + 180) % 360 - 180

            diff = wrapped_d_yaw
            diff = diff / (50.0 / self.throttle_sensitivity)
            diff *= right_ctr.axis2 ** 2

            print(rms_deriv)
            
            if ((diff > 0 and rms_deriv > self.throttle_yaw_inc_threshold) or
                (diff < 0 and rms_deriv > self.throttle_yaw_dec_threshold)):

                if diff > 0:
                    pass
                else:
                    diff *= 3 # TODO throttle decrease sensitivity

                self.throttle += diff
                self.throttle = min(1.0, max(0.0, self.throttle))

            if self.throttle > 0.05:
                amount = bezier_curve(self.throttle,
                    np.array([0, 0]),
                    np.array([0.6, 0]),
                    np.array([0, 1]),
                    np.array([1, 1]))[1]
                right_ctr.haptic([None, lambda t,f: amount if f%2==0 else 0])

        else:
            self.throttle_raw_yaws = None
            if self.throttle > 0.0:
                self.throttle -= self.get_update_delta() * self.throttle_decrease_per_second
                self.throttle = max(0.0, self.throttle)

        self.device.set_axis(HID_USAGE_RZ, int(self.throttle * 0x8000))

    def update_chaperone(self, chp):
        self.original_chaperone = chp
        self.current_chaperone = chp

    def update_grip(self, hand, ctr):

        grabber = self.hands_overlay.left_grab if hand == 'left' else self.hands_overlay.right_grab
        ungrabber = self.hands_overlay.left_ungrab if hand == 'left' else self.hands_overlay.right_ungrab

        if ctr.axis2 > 0:
            if self.grabbed[hand] == False:
                self.grabbed[hand] = True
                grabber()
        else:
            if self.grabbed[hand]:
                self.grabbed[hand] = False
                ungrabber()

    def update(self, left_ctr, right_ctr, hmd):
        super().update(left_ctr, right_ctr, hmd)

        # Hands
        if self.hands_overlay is None:
            self.hands_overlay = HandsImage(self.left_ctr, self.right_ctr)
            self.hands_overlay.closed_hands_always_top()
            
        # Update grip
        self.update_grip('left', left_ctr)
        self.update_grip('right', right_ctr)

        # Update max lean
        if self.config.bike_use_ac_server:
            self.max_lean = self.config.bike_max_lean * self.AC_CAL.max_lean_multiplier(self.ac_speed)

        # Update lean
        self._evaluate_lean_angle(left_ctr, right_ctr)

        # Throttle
        self._update_throttle(right_ctr)

        # vJoy
        lean_axis = self.lean/self.max_lean
        if self.config.bike_use_ac_server:
            lean_axis = self.AC_CAL.to_axis(lean_axis, self.ac_speed)
        
        axisX = int((lean_axis+1)/2.0 * 0x8000)
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

        left_ctr = self.left_ctr
        right_ctr = self.right_ctr

        self._edit_move_handlebar = False
        self._edit_last_l_pos = [left_ctr.x, left_ctr.y, left_ctr.z]
        self._edit_last_r_pos = [right_ctr.x, right_ctr.y, right_ctr.z]

        self.handlebar_image.set_alpha(1)

    def post_edit_mode(self):
        super().post_edit_mode()
        self.handlebar_image.set_color([1, 1, 1])

    def edit_mode(self, frames):
        super().edit_mode(frames)

        hmd = self.hmd
        left_ctr = self.left_ctr
        right_ctr = self.right_ctr
        now = time.time()

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
