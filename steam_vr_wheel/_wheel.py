from collections import deque
from math import pi, atan2, sin, cos, ceil, sqrt

import numpy as np
import openvr
import os
import copy
import time
import threading
import queue

from steam_vr_wheel._virtualpad import VirtualPad, RightTrackpadAxisDisablerMixin
from steam_vr_wheel.pyvjoy import HID_USAGE_X

def check_result(result):
    if result:
        error_name = openvr.VROverlay().getOverlayErrorNameFromEnum(result)
        raise Exception("OpenVR Error:", error_name)

def print_matrix(matrix):
    l = []
    for i in range(3):
        ll = []
        for j in range(4):
            ll.append(matrix[j])
        l.append(ll)
    print(l)

def rotation_matrix_around_vec(theta, vec):
    theta = theta * np.pi / 180
    m = sqrt(vec[0]**2 + vec[1]**2 + vec[2]**2)
    ux = vec[0]/m
    uy = vec[1]/m
    uz = vec[2]/m
    s, c = sin(theta), cos(theta)

    return np.array([[c+ux**2*(1-c), ux*uy*(1-c)-uz*s, ux*uz*(1-c)+uy*s],
                    [uy*ux*(1-c)+uz*s, c+uy**2*(1-c), uy*uz*(1-c)-ux*s],
                    [uz*ux*(1-c)-uy*s, uz*uy*(1-c)+ux*s, c+uz**2*(1-c)]])

def rotation_matrix(theta1, theta2, theta3):
    #https://programming-surgeon.com/en/euler-angle-python-en/
    c1 = np.cos(theta1 * np.pi / 180)
    s1 = np.sin(theta1 * np.pi / 180)
    c2 = np.cos(theta2 * np.pi / 180)
    s2 = np.sin(theta2 * np.pi / 180)
    c3 = np.cos(theta3 * np.pi / 180)
    s3 = np.sin(theta3 * np.pi / 180)

    return np.array([[c2*c3, -c2*s3, s2],
                         [c1*s3+c3*s1*s2, c1*c3-s1*s2*s3, -c2*s1],
                         [s1*s3-c1*c3*s2, c3*s1+c1*s2*s3, c1*c2]])

def initRotationMatrix(axis, angle, matrix=None):
    # angle in radians
    if matrix is None:
        matrix = openvr.HmdMatrix34_t()
    if axis==0:
        matrix.m[0][0] = 1.0
        matrix.m[0][1] = 0.0
        matrix.m[0][2] = 0.0
        matrix.m[0][3] = 0.0
        matrix.m[1][0] = 0.0
        matrix.m[1][1] = cos(angle)
        matrix.m[1][2] = -sin(angle)
        matrix.m[1][3] = 0.0
        matrix.m[2][0] = 0.0
        matrix.m[2][1] = sin(angle)
        matrix.m[2][2] = cos(angle)
        matrix.m[2][3] = 0.0
    elif axis==1:
        matrix.m[0][0] = cos(angle)
        matrix.m[0][1] = 0.0
        matrix.m[0][2] = sin(angle)
        matrix.m[0][3] = 0.0
        matrix.m[1][0] = 0.0
        matrix.m[1][1] = 1.0
        matrix.m[1][2] = 0.0
        matrix.m[1][3] = 0.0
        matrix.m[2][0] = -sin(angle)
        matrix.m[2][1] = 0.0
        matrix.m[2][2] = cos(angle)
        matrix.m[2][3] = 0.0
    elif axis == 2:
        matrix.m[0][0] = cos(angle)
        matrix.m[0][1] = -sin(angle)
        matrix.m[0][2] = 0.0
        matrix.m[0][3] = 0.0
        matrix.m[1][0] = sin(angle)
        matrix.m[1][1] = cos(angle)
        matrix.m[1][2] = 0.0
        matrix.m[1][3] = 0.0
        matrix.m[2][0] = 0.0
        matrix.m[2][1] = 0.0
        matrix.m[2][2] = 1.0
        matrix.m[2][3] = 0.0
    return matrix


def matMul33(a, b, result=None):
    if result is None:
        result = openvr.HmdMatrix34_t()
    for i in range(3):
        for j in range(3):
            result.m[i][j] = 0.0
            for k in range(3):
                result.m[i][j] += a.m[i][k] * b.m[k][j]
    result[0][3] = b[0][3]
    result[1][3] = b[1][3]
    result[2][3] = b[2][3]
    return result



class HandsImage:
    def __init__(self, left_ctr, right_ctr):
        self._handl_closed = False
        self._handr_closed = False
        self.left_ctr = left_ctr
        self.right_ctr = right_ctr
        hand_size = 0.14
        self.alpha = 0.9

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
        check_result(self.vroverlay.setOverlaySortOrder(self.l_ovr, 1))
        check_result(self.vroverlay.setOverlaySortOrder(self.l_ovr2, 1))
        check_result(self.vroverlay.setOverlaySortOrder(self.r_ovr, 1))
        check_result(self.vroverlay.setOverlaySortOrder(self.r_ovr2, 1))

        this_dir = os.path.abspath(os.path.dirname(__file__))

        self.l_open_png = os.path.join(this_dir, 'media', 'hand_open_l.png')
        self.r_open_png = os.path.join(this_dir, 'media', 'hand_open_r.png')
        self.l_close_png = os.path.join(this_dir, 'media', 'hand_closed_l.png')
        self.r_close_png = os.path.join(this_dir, 'media', 'hand_closed_r.png')

        check_result(self.vroverlay.setOverlayFromFile(self.l_ovr, self.l_open_png.encode()))
        check_result(self.vroverlay.setOverlayFromFile(self.l_ovr2, self.l_close_png.encode()))
        check_result(self.vroverlay.setOverlayFromFile(self.r_ovr, self.r_open_png.encode()))
        check_result(self.vroverlay.setOverlayFromFile(self.r_ovr2, self.r_close_png.encode()))

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
        ctr_tf[2][3] = 0

        self.ctr_tf = ctr_tf
        self.attach_to_ctr('left')
        self.attach_to_ctr('right')

        check_result(result)
        check_result(self.vroverlay.showOverlay(self.l_ovr))
        check_result(self.vroverlay.showOverlay(self.l_ovr2))
        check_result(self.vroverlay.showOverlay(self.r_ovr))
        check_result(self.vroverlay.showOverlay(self.r_ovr2))

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


class HShifterImage:
    def __init__(self, wheel, x=0.25, y=-0.57, z=-0.15, degree=15, scale=100, alpha=100):
        self.vrsys = openvr.VRSystem()
        self.vroverlay = openvr.IVROverlay()

        self.x = x
        self.y = y
        self.z = z
        self.size = 7 / 100
        self.degree = degree
        self.pos = 3.5
        self.wheel = wheel

        #self._button_queue = []
        self._snap_ctr = None
        self._snap_start_pos = False
        self._snapped = False
        self._snap_times = []
        self._snap_db_timer = None
        self._snap_ctr_offset = []
        self._snap_tf = None

        self._knob_pos = [0,0,0]

        self._splitter_toggled = False
        self._range_toggled = False

        self._pos_to_button = dict({1: 43, 3:   45, 5: 47,
                                           3.5: 42,
                                    2: 44, 4:   46, 6: 48})
        self._pressed_button = 42 #N
        self._xz = [0,0]
        self._last_xz_grid = np.array([0,0])

        # Create
        result, self.slot = self.vroverlay.createOverlay('hshifter_slot'.encode(), 'hshifter_slot'.encode())
        check_result(result)
        result, self.stick = self.vroverlay.createOverlay('hshifter_stick'.encode(), 'hshifter_stick'.encode())
        check_result(result)
        result, self.knob = self.vroverlay.createOverlay('hshifter_knob'.encode(), 'hshifter_knob'.encode())
        check_result(result)

        # Images
        this_dir = os.path.abspath(os.path.dirname(__file__))
        slot_img = os.path.join(this_dir, 'media', 'h_shifter_slot.png')
        self._stick_img = os.path.join(this_dir, 'media', 'h_shifter_stick_low.png')
        self._stick_img_2 = os.path.join(this_dir, 'media', 'h_shifter_stick_high.png')
        self._knob_img = os.path.join(this_dir, 'media', 'h_shifter_knob.png')
        self._knob_img_2 = os.path.join(this_dir, 'media', 'h_shifter_knob_over.png')

        check_result(self.vroverlay.setOverlayFromFile(self.slot, slot_img.encode()))
        check_result(self.vroverlay.setOverlayFromFile(self.stick, self._stick_img.encode()))
        check_result(self.vroverlay.setOverlayFromFile(self.knob, self._knob_img.encode()))

        # Visibility
        check_result(self.vroverlay.setOverlayColor(self.slot, 0.2, 0.2, 0.2)) # default gray outline
        check_result(self.vroverlay.setOverlayAlpha(self.slot, alpha/100))
        check_result(self.vroverlay.setOverlayWidthInMeters(self.slot, self.size)) # default 7cm
        
        stick_width = 0.02
        self.stick_width = stick_width
        txw, txh = 40, 633
        stick_height = txh / (txw / stick_width)
        stick_scale = scale / 100 # 1.0 => 31.65cm
        stick_height *= stick_scale
        check_result(self.vroverlay.setOverlayColor(self.stick, 1, 1, 1))
        check_result(self.vroverlay.setOverlayAlpha(self.stick, alpha/100))
        check_result(self.vroverlay.setOverlayWidthInMeters(self.stick, stick_width))

        check_result(self.vroverlay.setOverlayColor(self.knob, 1, 1, 1))
        check_result(self.vroverlay.setOverlayAlpha(self.knob, alpha/100))
        check_result(self.vroverlay.setOverlayWidthInMeters(self.knob, 0.05))

        def set_transform(tf, mat):
            for i in range(0, 3):
                for j in range(0, 4):
                    tf[i][j] = mat[i][j]

        # Position
        result, self.slot_tf = self.vroverlay.setOverlayTransformAbsolute(self.slot, openvr.TrackingUniverseSeated)
        check_result(result)
        set_transform(self.slot_tf, [[1.0, 0.0, 0.0, x],
                                    [0.0, 0.0, 1.0, y],
                                    [0.0, -1.0, 0.0, z]]) # 90deg at X

        result, self.stick_tf = self.vroverlay.setOverlayTransformAbsolute(self.stick, openvr.TrackingUniverseSeated)
        check_result(result)
        result, self.stick_uv = self.vroverlay.getOverlayTextureBounds(self.stick)
        check_result(result)
        set_transform(self.stick_tf, [[1.0, 0.0, 0.0, x],
                                    [0.0, stick_scale, 0.0, y+stick_height/2],
                                    [0.0, 0.0, 1.0, z]])
        self.stick_uv.vMax = stick_scale
        self.stick_height = stick_height
        self.stick_scale = stick_scale
        check_result(self.vroverlay.function_table.setOverlayTextureBounds(self.stick, openvr.byref(self.stick_uv)))

        result, self.knob_tf = self.vroverlay.setOverlayTransformAbsolute(self.knob, openvr.TrackingUniverseSeated)
        check_result(result)
        set_transform(self.knob_tf, [[1.0, 0.0, 0.0, x],
                                    [0.0, 1.0, 0.0, y+stick_height],
                                    [0.0, 0.0, 1.0, z]])

        # Final
        fn = self.vroverlay.function_table.setOverlayTransformAbsolute
        result = fn(self.slot, openvr.TrackingUniverseSeated, openvr.byref(self.slot_tf))
        result = fn(self.stick, openvr.TrackingUniverseSeated, openvr.byref(self.stick_tf))
        result = fn(self.knob, openvr.TrackingUniverseSeated, openvr.byref(self.knob_tf))
        check_result(self.vroverlay.showOverlay(self.slot))
        check_result(self.vroverlay.showOverlay(self.stick))
        check_result(self.vroverlay.showOverlay(self.knob))

        check_result(self.vroverlay.setOverlaySortOrder(self.stick, 1))
        check_result(self.vroverlay.setOverlaySortOrder(self.knob, 1))

        # Get HMD id for yaw
        vrsys = openvr.VRSystem()
        for i in range(openvr.k_unMaxTrackedDeviceCount):
            device_class = vrsys.getTrackedDeviceClass(i)
            if device_class == openvr.TrackedDeviceClass_HMD:
                self._hmd_id = i
        poses_t = openvr.TrackedDevicePose_t * openvr.k_unMaxTrackedDeviceCount
        self._poses = poses_t()

        self.last_pos = 3.5

    def check_collision(self, ctr):
        x, y, z = ctr.x, ctr.y, ctr.z
        pm, pM = self.bounds
        x0, y0, z0 = pm
        x2, y2, z2 = pM
        
        return x0<=x<=x2 and y0<=y<=y2 and z0<=z<=z2

    def _get_hmd_rot(self):
        openvr.VRSystem().getDeviceToAbsoluteTrackingPose(openvr.TrackingUniverseSeated, 0, len(self._poses), self._poses)
        m = self._poses[self._hmd_id].mDeviceToAbsoluteTracking
        R = np.array([[m[0][0], m[1][0], m[2][0]],
            [m[0][1], m[1][1], m[2][1]],
            [m[0][2], m[1][2], m[2][2]]])
        #https://learnopencv.com/rotation-matrix-to-euler-angles/
        sy = sqrt(R[0,0] * R[0,0] +  R[1,0] * R[1,0])
     
        singular = sy < 1e-6
     
        if not singular :
            x = atan2(R[2,1] , R[2,2])
            y = atan2(-R[2,0], sy)
            z = atan2(R[1,0], R[0,0])
        else :
            x = atan2(-R[1,2], R[1,1])
            y = atan2(-R[2,0], sy)
            z = 0
        return [x/pi*180, y/pi*180, z/pi*180]

    def set_stick_xz_pos(self, xz_pos, ctr=None):
        
        """
        |1  |3  |5  |  43 45 47
        |1.5|3.5|5.5|     42
        |2  |4  |6  |  44 46 48

        double tap 49  triple tap 50
        """
        self.pos = xz_pos[0]*2+3 + (xz_pos[1]+1)/2

        is_button = self.pos in self._pos_to_button

        # Position that has button mapping
        if is_button:
            btn_id = self._pos_to_button[self.pos]
            self._pressed_button = btn_id

    def toggle_splitter(self, ctr):
        self._splitter_toggled = not self._splitter_toggled
        check_result(self.vroverlay.setOverlayFromFile(self.knob, 
            self._knob_img_2.encode() if self._splitter_toggled else self._knob_img.encode()))

        def haptic():
            openvr.VRSystem().triggerHapticPulse(ctr.id, 0, 3000)
            time.sleep(0.16)
            openvr.VRSystem().triggerHapticPulse(ctr.id, 0, 3000)
        t = threading.Thread(target=haptic)
        t.start()

    def toggle_range(self, ctr):
        self._range_toggled = not self._range_toggled
        check_result(self.vroverlay.setOverlayFromFile(self.stick,
            self._stick_img_2.encode() if self._range_toggled else self._stick_img.encode()))

        def haptic():
            for i in range(16):
                openvr.VRSystem().triggerHapticPulse(ctr.id, 0, 3000)
                time.sleep(0.02)
        t = threading.Thread(target=haptic)
        t.start()

    def snap_ctr(self, ctr):
        now = time.time()
        self._snap_ctr = ctr
        self._snap_ctr_offset = [ctr.x - self._knob_pos[0], ctr.y - self._knob_pos[1], ctr.z - self._knob_pos[2]]
        self._snapped = True


        return

        # Check double tap
        self._snap_times.append(now)
        self._snap_times = self._snap_times[-3:]

        if len(self._snap_times) >= 3 and self._snap_times[-1] - self._snap_times[-3] <= 1.0:

            self._snap_db_timer.cancel()
            self._snap_times = []

            #self.wheel.device.set_button(50, True)
            #self._button_queue.append([50, time.time()])
            self._range_toggled = not self._range_toggled
            check_result(self.vroverlay.setOverlayFromFile(self.stick,
                self._stick_img_2.encode() if self._range_toggled else self._stick_img.encode()))

            def haptic():
                for i in range(16):
                    openvr.VRSystem().triggerHapticPulse(ctr.id, 0, 3000)
                    time.sleep(0.02)
            t = threading.Thread(target=haptic)
            t.run()

        elif len(self._snap_times) >= 2 and self._snap_times[-1] - self._snap_times[-2] <= 0.5:
            def wait_for_third():
                self._snap_times = []

                #self.wheel.device.set_button(49, True)
                #self._button_queue.append([49, time.time()])
                self._splitter_toggled = not self._splitter_toggled
                check_result(self.vroverlay.setOverlayFromFile(self.knob, 
                    self._knob_img_2.encode() if self._splitter_toggled else self._knob_img.encode()))
                def haptic():
                    openvr.VRSystem().triggerHapticPulse(ctr.id, 0, 3000)
                    time.sleep(0.16)
                    openvr.VRSystem().triggerHapticPulse(ctr.id, 0, 3000)
                t = threading.Thread(target=haptic)
                t.run()
            self._snap_db_timer = threading.Timer(0.35, wait_for_third)
            self._snap_db_timer.start()

    def unsnap(self):
        self._snapped = False
        if self.pos == 1.5 or self.pos == 5.5:
            self.set_stick_xz_pos([0,0])

        self._move_stick(self._xz_pos())

        """
        |1  |3  |5  |  1 3 5
        |1.5|3.5|5.5|  +-N-+
        |2  |4  |6  |  2 4 6

        odd: towards -z
        x2 is odd: no rotation
        even: towards +z

        x = (round(pos/2)-1) * ...
        z_rot = ((pos%2 if pos%2 != 0 else 2)-1.5) * ...
        """

    def _xz_pos(self):
        return [(ceil(self.pos/2)-2), ((self.pos%2 if self.pos%2 != 0 else 2)-1.5)*2]

    def _move_stick(self, xz):
        self._xz = xz

    def render(self):
        # xz = relative and normalized
        xz = self._xz
        pitch, yaw, roll = self._get_hmd_rot()

        unit = (self.size/2 - self.stick_width/2)

        x_deg = self.degree * abs(xz[0])
        z_deg = self.degree * abs(xz[1])
        x_sin = sin(x_deg*pi/180) * self.stick_height
        z_sin = sin(z_deg*pi/180) * self.stick_height
        x_knob = self.x + xz[0] * (x_sin + unit)
        z_knob = self.z + xz[1] * (z_sin + unit)
        x_stick = self.x + xz[0] * unit
        z_stick = self.z + xz[1] * unit
        rot_knob = rotation_matrix(0, -yaw, 0)
        rot_stick = rotation_matrix(xz[1] * z_deg, 0, xz[0] * -x_deg)

        y_knob = (self.y + self.stick_height - 
            (abs(xz[1])*((1-cos((z_deg)*pi/180))*self.stick_height)) -
            (abs(xz[0])*((1-cos((x_deg)*pi/180))*self.stick_height))
            )

        def rot_dot_tf(rot, hmd34, local=None):
            tf = np.eye(4)
            for i in range(3):
                tf[i][3] = hmd34[i][3] # discard original rot

            r = np.eye(4)
            r[0:3, 0:3] = rot
            d = np.dot(tf, r)

            if local is not None:
                r[0:3, 0:3] = local
                d = np.dot(d, r)

            for i in range(3):
                for j in range(4):
                    hmd34[i][j] = d[i,j]

        self._knob_pos[0] = x_knob
        self._knob_pos[1] = y_knob
        self._knob_pos[2] = z_knob
        self.knob_tf[0][3] = x_knob
        self.knob_tf[1][3] = y_knob
        self.knob_tf[2][3] = z_knob
        rot_dot_tf(rot_knob, self.knob_tf)

        offset_stick = np.dot(rot_stick, (0, self.stick_height/2, 0))
        self.stick_tf[0][3] = x_stick + offset_stick[0]
        self.stick_tf[1][3] = self.y + offset_stick[1]
        self.stick_tf[2][3] = z_stick + offset_stick[2]
        scale_stick = np.eye(3)
        scale_stick[2,2] = self.stick_scale
        local_stick = np.dot(scale_stick, rot_knob) 
        rot_dot_tf(rot_stick, self.stick_tf, local_stick)

        self.slot_tf[0][3] = self.x
        self.slot_tf[1][3] = self.y
        self.slot_tf[2][3] = self.z

        # Bounds
        self.bounds = [
            [self.x - x_sin-unit-0.065, self.y+self.stick_height-0.16, self.z -z_sin-unit-0.08], 
            [self.x + x_sin+unit+0.065, self.y+self.stick_height+0.08, self.z +z_sin+unit+0.08]]
        """
        self.bounds = [
            [x_knob-0.08, self.y+self.stick_height-0.16, z_knob-0.08], 
            [x_knob+0.08, self.y+self.stick_height+0.08, z_knob+0.08]]
        """

        # Set snap transform
        ctr = self._snap_ctr
        self._snap_tf = openvr.HmdMatrix34_t()
        self._snap_tf[0][3] = x_knob
        self._snap_tf[1][3] = y_knob
        self._snap_tf[2][3] = z_knob
        rot_dot_tf(rot_knob, self._snap_tf)

        fn = self.vroverlay.function_table.setOverlayTransformAbsolute
        fn(self.slot, openvr.TrackingUniverseSeated, openvr.byref(self.slot_tf))
        fn(self.stick, openvr.TrackingUniverseSeated, openvr.byref(self.stick_tf))
        fn(self.knob, openvr.TrackingUniverseSeated, openvr.byref(self.knob_tf))

    def attach_hand(self, hand, left_ctr=None, right_ctr=None):
        self.wheel.hands_overlay.move(hand, self._snap_tf)

    def set_color(self, cl):
        check_result(self.vroverlay.setOverlayColor(self.knob, *cl))
        check_result(self.vroverlay.setOverlayColor(self.stick, *cl))

    def move_delta(self, d):
        self.x += d[0]
        self.y += d[1]
        self.z += d[2]
        self.wheel.config.shifter_center = [self.x, self.y, self.z]

    def update(self):

        for v in self._pos_to_button.values():
            if v != self._pressed_button:
                self.wheel.device.set_button(v, False)
        self.wheel.device.set_button(self._pressed_button, True)

        # Toggles
        self.wheel.device.set_button(49, self._splitter_toggled)
        self.wheel.device.set_button(50, self._range_toggled)

        if self._snapped:
            u_sin = (self.stick_height * sin(self.degree*pi/180))
            unit = (self.size/2 - self.stick_width/2)

            ctr = self._snap_ctr
            p1 = [ctr.x, ctr.y, ctr.z]
            p1[0] -= self._snap_ctr_offset[0]
            #p1[1] -= self._snap_ctr_offset[1]
            p1[2] -= self._snap_ctr_offset[2]

            dp_unsafe = (p1[0]-self.x, 0, p1[2]-self.z)
            xz_ctr = np.array([
                max(min(dp_unsafe[0] / (u_sin + unit), 1.0), -1.0),
                max(min(dp_unsafe[2] / (u_sin + unit), 1.0), -1.0)])

            x_mid_margin = 0.55
            z_end_margin = 0.8
            z_mid_margin = 0.7

            in_middle = abs(xz_ctr[1]) <= z_mid_margin
            if x_mid_margin < abs(xz_ctr[0]) < 1 and not in_middle:
                openvr.VRSystem().triggerHapticPulse(ctr.id, 0, 1500)

            xz_pos_0 = self._xz_pos()
            xz_pos_1 = xz_pos_0.copy()
            xz_0 = self._xz
            xz_1 = xz_0.copy()
            if in_middle:
                xz_1[0] = xz_ctr[0]
                xz_1[1] = xz_ctr[1]
                if xz_ctr[0] == -1:
                    xz_1[0] = -1
                    xz_pos_1[0] = -1
                elif xz_ctr[0] == 1:
                    xz_1[0] = 1
                    xz_pos_1[0] = 1
                elif abs(xz_ctr[0]) <= x_mid_margin:
                    xz_1[0] = 0
                    xz_pos_1[0] = 0
                else:
                    xz_1[1] = 0
            else:
                xz_1[0] = xz_pos_0[0]
                xz_1[1] = xz_ctr[1]
                if xz_ctr[1] < -z_end_margin:
                    xz_pos_1[1] = -1
                elif xz_ctr[1] > z_end_margin:
                    xz_pos_1[1] = 1
                else:
                    xz_pos_1[1] = 0

            if xz_pos_0 != xz_pos_1 and xz_pos_1[1] != 0:
                openvr.VRSystem().triggerHapticPulse(ctr.id, 0, 3000)

            self._move_stick(xz_1)
            self.set_stick_xz_pos(xz_pos_1)


class SteeringWheelImage:
    def __init__(self, x=0, y=-0.4, z=-0.35, size=0.55, alpha=1):
        self.vrsys = openvr.VRSystem()
        self.vroverlay = openvr.IVROverlay()
        result, self.wheel = self.vroverlay.createOverlay('keyiiii'.encode(), 'keyiiii'.encode())
        check_result(result)

        check_result(self.vroverlay.setOverlayColor(self.wheel, 1, 1, 1))
        check_result(self.vroverlay.setOverlayAlpha(self.wheel, alpha))
        check_result(self.vroverlay.setOverlayWidthInMeters(self.wheel, size))

        this_dir = os.path.abspath(os.path.dirname(__file__))
        wheel_img = os.path.join(this_dir, 'media', 'steering_wheel.png')

        check_result(self.vroverlay.setOverlayFromFile(self.wheel, wheel_img.encode()))


        result, transform = self.vroverlay.setOverlayTransformAbsolute(self.wheel, openvr.TrackingUniverseSeated)

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
        result = fn(self.wheel, openvr.TrackingUniverseSeated, openvr.byref(pmatTrackingOriginToOverlayTransform))

        check_result(result)
        check_result(self.vroverlay.showOverlay(self.wheel))

    def set_color(self, cl):
        check_result(self.vroverlay.setOverlayColor(self.wheel, *cl))

    def set_alpha(self, alpha):
        check_result(self.vroverlay.setOverlayAlpha(self.wheel, alpha))

    def move(self, point, size):
        self.transform[0][3] = point.x
        self.transform[1][3] = point.y
        self.transform[2][3] = point.z
        #print(point.x, point.y, point.z)
        self.size = size
        fn = self.vroverlay.function_table.setOverlayTransformAbsolute
        fn(self.wheel, openvr.TrackingUniverseSeated, openvr.byref(self.transform))
        check_result(self.vroverlay.setOverlayWidthInMeters(self.wheel, size))

    def rotate(self, angles, axis=[2,]):
        try:
            self.rotation_matrix
        except AttributeError:
            self.rotation_matrix = openvr.HmdMatrix34_t()
        if not isinstance(angles, list):
            angles = [angles, ]

        if not isinstance(axis, list):
            axis = [axis, ]

        result = copy.copy(self.transform)
        for angle, ax in zip(angles, axis):
            initRotationMatrix(ax, -angle, self.rotation_matrix)
            result = matMul33(self.rotation_matrix, result)

        fn = self.vroverlay.function_table.setOverlayTransformAbsolute
        fn(self.wheel, openvr.TrackingUniverseSeated, openvr.byref(result))

    def hide(self):
        check_result(self.vroverlay.hideOverlay(self.wheel))

    def show(self):
        check_result(self.vroverlay.showOverlay(self.wheel))



class Point:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

class GrabControllerPoint(Point):
    def __init__(self, x, y, z, id=0):
        super().__init__(x, y, z)
        self.id = id


class Wheel(RightTrackpadAxisDisablerMixin, VirtualPad):
    def __init__(self, inertia=0.95, center_speed=pi/180):
        super().__init__()
        self.vrsys = openvr.VRSystem()
        self.hands_overlay = None
        self.is_edit_mode = False
        x, y, z = self.config.wheel_center
        size = self.config.wheel_size
        self._inertia = inertia
        self._center_speed = center_speed  # radians per frame, force which returns wheel to center when not grabbed
        self._center_speed_coeff = 1  # might be calculated later using game telemetry
        self.x = 0  # -1 0 1
        self._wheel_angles = deque(maxlen=10)
        self._wheel_angles.append(0)
        self._wheel_angles.append(0)
        self._snapped = False

        self._rot = rotation_matrix(-self.config.wheel_pitch, 0, 0)
        self._rot_inv = rotation_matrix(self.config.wheel_pitch, 0, 0)

        # radians per frame last turn speed when wheel was being held, gradually decreases after wheel is released
        self._turn_speed = 0

        self.wheel_image = SteeringWheelImage(x=x, y=y, z=z, size=size, alpha=self.config.wheel_alpha)
        self.center = Point(x, y, z)
        self.size = size
        self._grab_started_point = None
        self._wheel_grab_offset = 0

        # for manual grab:
        self._grip_queue = queue.Queue()
        self._hand_snaps = dict({'left': '', 'right': ''})

        # for auto grab
        self._last_left_in_holding = False
        self._last_right_in_holding = False

        # for triple grip:
        self._grip_times = dict({'left': [], 'right': []})

        # edit mode
        self._edit_mode_last_press = 0.0
        self._edit_mode_entry = 0.0

        # H Shifter
        s_c = self.config.shifter_center
        self.h_shifter_image = HShifterImage(self, x=s_c[0], y=s_c[1], z=s_c[2],
                            alpha=self.config.shifter_alpha,
                            scale=self.config.shifter_scale,
                            degree=self.config.shifter_degree)
        self._last_knob_haptic = 0

    def point_in_holding_bounds(self, point):
        point = self.to_wheel_space(point)

        a = self.size/2 + 0.06
        b = self.size/2 - 0.10
        if self.config.vertical_wheel:
            x = point.x - self.center.x
            y = point.y - self.center.y
            z = point.z - self.center.z
        else:
            z = point.y - self.center.y
            y = point.x - self.center.x
            x = point.z - self.center.z

        if abs(z) < 0.075:
            distance = sqrt(x**2+y**2)
            if distance < b:
                return False
            if distance < a:
                return True
        else:
            return False

    def _subtract_and_rotate(self, point, mat):
        diff = np.array([point.x-self.center.x,
                        point.y-self.center.y,
                        point.z-self.center.z])
        l = np.dot(mat, diff)
        l[0] += self.center.x
        l[1] += self.center.y
        l[2] += self.center.z
        return Point(l[0], l[1], l[2])

    def to_wheel_space(self, point):
        return self._subtract_and_rotate(point, self._rot_inv)

    def to_absolute_space(self, point):
        return self._subtract_and_rotate(point, self._rot)

    def unwrap_wheel_angles(self):
        period = 2 * pi
        angle = np.array(self._wheel_angles, dtype=float)
        diff = np.diff(angle)
        diff_to_correct = (diff + period / 2.) % period - period / 2.
        increment = np.cumsum(diff_to_correct - diff)
        angle[1:] += increment
        self._wheel_angles[-1] = angle[-1]

    def wheel_raw_angle(self, point):
        point = self.to_wheel_space(point)
        a = float(point.y) - self.center.y
        b = float(point.x) - self.center.x

        angle = atan2(a, b)
        return angle

    def wheel_double_raw_angle(self, left_ctr, right_ctr):
        left_ctr = self.to_wheel_space(left_ctr)
        right_ctr = self.to_wheel_space(right_ctr)
        a = left_ctr.y - right_ctr.y
        b = left_ctr.x - right_ctr.x

        return atan2(a, b)

    def ready_to_unsnap(self, l, r):
        l = self.to_wheel_space(l)
        r = self.to_wheel_space(r)

        d = (l.x - r.x)**2 + (l.y - r.y)**2 + (l.z - r.z)**2

        if d > self.size**2:
            return True

        dc = ((self.center.x - (l.x+r.x)/2)**2
              + (self.center.y - (l.y+r.y)/2)**2
              + (self.center.z - (l.z+r.z)/2)**2
              )
        if dc > self.size**2:
            return True

        return False

    def set_button_unpress(self, button, hand):
        super().set_button_unpress(button, hand)
        if self.config.wheel_grabbed_by_grip_toggle:
            if button == openvr.k_EButton_Grip and hand == 'left':
                self._grip_queue.put(['left', False])

            if button == openvr.k_EButton_Grip and hand == 'right':
                self._grip_queue.put(['right', False])
        else:
            pass

    def set_button_press(self, button, hand, left_ctr, right_ctr):
        ctr = left_ctr if hand == 'left' else right_ctr

        if self._hand_snaps[hand] == 'shifter':
            if button == openvr.k_EButton_SteamVR_Trigger:
                self.h_shifter_image.toggle_range(ctr)
            elif button == openvr.k_EButton_A:
                self.h_shifter_image.toggle_splitter(ctr)
        else:
            super().set_button_press(button, hand)

        if button == openvr.k_EButton_Grip and hand == 'left':
            if self.config.wheel_grabbed_by_grip_toggle:
                self._grip_queue.put(['left', True])
            else:
                self._grip_queue.put(['left', self._hand_snaps['left'] == ''])

        if button == openvr.k_EButton_Grip and hand == 'right':
            if self.config.wheel_grabbed_by_grip_toggle:
                self._grip_queue.put(['right', True])
            else:
                self._grip_queue.put(['right', self._hand_snaps['right'] == ''])


    def _wheel_update(self, left_ctr, right_ctr):
        left_bound = self._hand_snaps['left'][:5] == 'wheel'
        right_bound = self._hand_snaps['right'][:5] == 'wheel'

        if right_bound and left_bound and not self._snapped:
            self.is_held([left_ctr, right_ctr])

        if self._snapped:
            angle = self.wheel_double_raw_angle(left_ctr, right_ctr) + self._wheel_grab_offset
            return angle

        if right_bound:
            controller = right_ctr
            self.is_held(controller)
        elif left_bound:
            controller = left_ctr
            self.is_held(controller)
        else:
            self.is_not_held()
            return None
        angle = self.wheel_raw_angle(controller) + self._wheel_grab_offset
        return angle

    def calculate_grab_offset(self, raw_angle=None):
        if raw_angle is None:
            raw_angle = self.wheel_raw_angle(self._grab_started_point)
        self._wheel_grab_offset = self._wheel_angles[-1] - raw_angle

    def is_held(self, controller):

        if isinstance(controller, list):
            self._snapped = True
            angle = self.wheel_double_raw_angle(controller[0], controller[1])
            self.calculate_grab_offset(angle)
            self._grab_started_point = None
            return

        if self._grab_started_point is None or self._grab_started_point.id != controller.id:
            self._grab_started_point = GrabControllerPoint(controller.x, controller.y, controller.z, controller.id)
            self.calculate_grab_offset()

    def is_not_held(self):
        self._grab_started_point = None

    def inertia(self):
        if self._grab_started_point:
            self._turn_speed = self._wheel_angles[-1] - self._wheel_angles[-2]
        else:
            self._wheel_angles.append(self._wheel_angles[-1] + self._turn_speed)
            self._turn_speed *= self._inertia

    def center_force(self):
        angle = self._wheel_angles[-1]
        sign = 1
        if angle < 0:
            sign = -1
        if abs(angle) < self._center_speed * self.config.wheel_centerforce:
            self._wheel_angles[-1] = 0
            return
        self._wheel_angles[-1] -= self._center_speed * self.config.wheel_centerforce * sign

    def send_to_vjoy(self):
        wheel_turn = self._wheel_angles[-1] / (2 * pi)
        axisX = int((-wheel_turn / (self.config.wheel_degrees / 360) + 0.5) * 0x8000)
        self.device.set_axis(HID_USAGE_X, axisX)

    def render(self):
        wheel_angle = self._wheel_angles[-1]
        if self.config.vertical_wheel:
            self.wheel_image.rotate([-wheel_angle, self.config.wheel_pitch*pi/180], [2, 0])
        else:
            self.wheel_image.rotate([-wheel_angle, np.pi / 2], [2, 0])

        # Switch alpha
        self.wheel_image.set_alpha(self.config.wheel_alpha / 100.0)

    def limiter(self, left_ctr, right_ctr):
        if abs(self._wheel_angles[-1])/(2*pi)>(self.config.wheel_degrees / 360)/2:
            self._wheel_angles[-1] = self._wheel_angles[-2]
            openvr.VRSystem().triggerHapticPulse(left_ctr.id, 0, 3000)
            openvr.VRSystem().triggerHapticPulse(right_ctr.id, 0, 3000)

    def _wheel_update_common(self, angle, left_ctr, right_ctr):
        if angle:
            self._wheel_angles.append(angle)

        self.unwrap_wheel_angles()

        self.inertia()
        if (not self._hand_snaps['left'][:5] == 'wheel') and (not self._hand_snaps['right'][:5] == 'wheel'):
            self.center_force()
        self.limiter(left_ctr, right_ctr)
        self.send_to_vjoy()

    def attach_hand(self, hand, left_ctr, right_ctr):
        left_ctr = self.to_wheel_space(left_ctr)
        right_ctr = self.to_wheel_space(right_ctr)

        ctr = left_ctr if hand == 'left' else right_ctr
        offset = [ctr.x - self.center.x, ctr.y - self.center.y]
        a = sqrt(offset[0]**2 + offset[1]**2)/(self.size/2)
        offset[0] /= a
        offset[1] /= a
        tf = openvr.HmdMatrix34_t()
        for i in range(3):
            for j in range(3):
                tf[i][j] = self._rot[i][j]

        tf[0][3] = self.center.x + offset[0]
        tf[1][3] = self.center.y + offset[1]
        tf[2][3] = self.center.z + 0.02

        ab = self.to_absolute_space(Point(tf[0][3], tf[1][3], tf[2][3]))

        tf[0][3] = ab.x
        tf[1][3] = ab.y
        tf[2][3] = ab.z

        self.hands_overlay.move(hand, tf)

    def _reset_hands(self):
        self._hand_snaps['left'] = ''
        self._hand_snaps['right'] = ''
        self.hands_overlay.attach_to_ctr('left')
        self.hands_overlay.attach_to_ctr('right')
        self.hands_overlay.left_ungrab()
        self.hands_overlay.right_ungrab()
        while not self._grip_queue.empty():
            self._grip_queue.get()

    GRIP_FLAG_AUTO_GRAB = 0x1

    def _update_hands(self, grip_info, left_ctr, right_ctr):
        hand = grip_info[0]
        flag = 0 if len(grip_info) < 3 else grip_info[2]

        ctr = left_ctr if hand == 'left' else right_ctr
        grabber = self.hands_overlay.left_grab if hand == 'left' else self.hands_overlay.right_grab
        ungrabber = self.hands_overlay.left_ungrab if hand == 'left' else self.hands_overlay.right_ungrab
        other = 'left' if hand == 'right' else 'right'

        # Handle triple grips for edit mode
        if grip_info[1] == True and flag == 0:
            now = time.time()
            self._grip_times[hand].append(now)
            self._grip_times[hand] = self._grip_times[hand][-3:]

            if (len(self._grip_times[hand]) >= 3 and
                len(self._grip_times[other]) >= 3 and
                self._grip_times[hand][-1] - self._grip_times[hand][-3] <= 1.0 and
                self._grip_times[other][-1] - self._grip_times[other][-3] <= 1.0):

                self._grip_times[hand] = []
                self._grip_times[other] = []

                openvr.VRSystem().triggerHapticPulse(left_ctr.id, 0, 3000)
                openvr.VRSystem().triggerHapticPulse(right_ctr.id, 0, 3000)

                self._reset_hands()
                self.is_edit_mode = True
                self._edit_mode_entry = time.time()
                return

        if grip_info[1] == False:
            if self._hand_snaps[hand][:5] == 'wheel':
                self._snapped = False
            elif self._hand_snaps[hand] == 'shifter':
                self.h_shifter_image.unsnap()

            self.hands_overlay.attach_to_ctr(hand)
            ungrabber()
            self._hand_snaps[hand] = ''
        else:
            if self._hand_snaps[hand] == 'wheel_auto':
                self._hand_snaps[hand] = 'wheel'
                return
            if self._hand_snaps[hand] != '':
                return

            grabber()
            if self.h_shifter_image.check_collision(ctr) and (flag & self.GRIP_FLAG_AUTO_GRAB == 0):
                self._hand_snaps[hand] = 'shifter'
                self.h_shifter_image.snap_ctr(ctr)
                openvr.VRSystem().triggerHapticPulse(ctr.id, 0, 300)
            else:
                self._hand_snaps[hand] = 'wheel' if (flag & self.GRIP_FLAG_AUTO_GRAB == 0) else 'wheel_auto'

    def update(self, left_ctr, right_ctr):
        if self.hands_overlay is None:
            self.hands_overlay = HandsImage(left_ctr, right_ctr)
        super().update(left_ctr, right_ctr)

        now = time.time()

        # Check hands
        while not self._grip_queue.empty():
            self._update_hands(self._grip_queue.get(), left_ctr, right_ctr)

        # Check for automatic grabbing
        if self.config.wheel_grabbed_by_grip:
            pass
        else:
            lh = self.point_in_holding_bounds(left_ctr)
            rh = self.point_in_holding_bounds(right_ctr)

            if self._last_left_in_holding != lh:
                if lh:
                    self._grip_queue.put(['left', True, self.GRIP_FLAG_AUTO_GRAB])
                elif self._hand_snaps['left'] == 'wheel_auto':
                    self._grip_queue.put(['left', False])

            if self._last_right_in_holding != rh:
                if rh:
                    self._grip_queue.put(['right', True, self.GRIP_FLAG_AUTO_GRAB])
                elif self._hand_snaps['right'] == 'wheel_auto':
                    self._grip_queue.put(['right', False])

            if self.ready_to_unsnap(left_ctr, right_ctr):
                self._snapped = False

            self._last_left_in_holding = lh
            self._last_right_in_holding = rh

        # Update hand transform
        for i in self._hand_snaps.items():
            hand = i[0]
            obj = i[1]
            if obj == 'wheel':
                self.attach_hand(hand, left_ctr, right_ctr)
            elif obj == 'shifter':
                self.h_shifter_image.attach_hand(hand)

        angle = self._wheel_update(left_ctr, right_ctr)

        self._wheel_update_common(angle, left_ctr, right_ctr)

        self.render()
        self.h_shifter_image.render()
        self.h_shifter_image.update()

        # Slight haptic when touching knob
        if self._hand_snaps['left'] != 'shifter' and self._hand_snaps['right'] != 'shifter':
            if now - self._last_knob_haptic > 0.25:
                self._last_knob_haptic = now
                if self._hand_snaps['left'] == '' and self.h_shifter_image.check_collision(left_ctr):
                    openvr.VRSystem().triggerHapticPulse(left_ctr.id, 0, 100)
                if self._hand_snaps['right'] == '' and self.h_shifter_image.check_collision(right_ctr):
                    openvr.VRSystem().triggerHapticPulse(right_ctr.id, 0, 100)

    def move_wheel(self, right_ctr, left_ctr):
        self.center = Point(right_ctr.x, right_ctr.y, right_ctr.z)
        self.config.wheel_center = [self.center.x, self.center.y, self.center.z]
        size = ((right_ctr.x-left_ctr.x)**2 +(right_ctr.y-left_ctr.y)**2 + (right_ctr.z-left_ctr.z)**2 )**0.5*2
        self.config.wheel_size = size
        self.size = size
        self.wheel_image.move(self.center, size)

    def move_delta(self, d):
        self.center = Point(self.center.x + d[0], self.center.y + d[1], self.center.z + d[2])
        self.config.wheel_center = [self.center.x, self.center.y, self.center.z]
        self.wheel_image.move(self.center, self.size)

    def resize_delta(self, d):
        if self.size + d < 0.10:
            return
        self.size += d
        self.config.wheel_size = self.size
        self.wheel_image.move(self.center, self.size)

    def pitch_delta(self, d):
        self.config.wheel_pitch += d
        self.config.wheel_pitch %= 360
        self._rot = rotation_matrix(-self.config.wheel_pitch, 0, 0)
        self._rot_inv = rotation_matrix(self.config.wheel_pitch, 0, 0)

    def discard_x(self):
        self.center = Point(0, self.center.y, self.center.z)
        self.config.wheel_center = [self.center.x, self.center.y, self.center.z]
        self.wheel_image.move(self.center, self.size)

    def edit_mode(self, left_ctr, right_ctr):

        result, state_r = openvr.VRSystem().getControllerState(right_ctr.id)
        now = time.time()

        if hasattr(self, "_edit_check") == False:
            self._edit_check = True
            self._edit_move_wheel = False
            self._edit_move_shifter = False
            self._edit_last_l_pos = [left_ctr.x, left_ctr.y, left_ctr.z]
            self._edit_last_r_pos = [right_ctr.x, right_ctr.y, right_ctr.z]
            self._edit_last_trigger_press = 0

        if self.hands_overlay != None:
            self.hands_overlay.show()
        if self.wheel_image != None:
            self.wheel_image.show()

        self.h_shifter_image.render()

        r_d = [right_ctr.x-self._edit_last_r_pos[0], right_ctr.y-self._edit_last_r_pos[1], right_ctr.z-self._edit_last_r_pos[2]]

        if self._edit_move_wheel:
            #self.move_wheel(right_ctr, left_ctr)
            self.move_delta(r_d)
            self.wheel_image.set_color((1,0,0))
        else:
            self.wheel_image.set_color((0,1,0))

        if self._edit_move_shifter:
            self.h_shifter_image.move_delta(r_d)
            self.h_shifter_image.set_color((1,0,0))
        else:
            self.h_shifter_image.set_color((0,1,0))

        def distance(p0):
            return sqrt((p0.x-right_ctr.x)**2 + (p0.y-right_ctr.y)**2 + (p0.z-right_ctr.z)**2)

        # Todo: switch alpha, shows the alpha-applied wheel for a second and after that set alpha to 1

        # EVRControllerAxisType
       # k_eControllerAxis_None = 0, 
       # k_eControllerAxis_TrackPad = 1,
       # k_eControllerAxis_Joystick = 2,
       # k_eControllerAxis_Trigger = 3, // Analog trigger data is in the X axis
        # rAxis
        if state_r.rAxis:
            x = state_r.rAxis[0].x # quest 2 joystick
            y = state_r.rAxis[0].y
            if self._edit_move_wheel:
                def dead_and_stretch(v, d):
                    if abs(v) < d:
                        return 0.0
                    else:
                        s = v / abs(v)
                        return (v - s*d)/(1-d)
                self.resize_delta(dead_and_stretch(x, 0.3) / 30)
                self.pitch_delta(dead_and_stretch(y, 0.75) * 2)
                self.render()

        if state_r.ulButtonPressed:
            btns = list(reversed(bin(state_r.ulButtonPressed)[2:]))
            btn_id = btns.index('1')
            if btn_id == openvr.k_EButton_SteamVR_Trigger:
                if now - self._edit_last_trigger_press > 0.2:
                    if self.h_shifter_image.check_collision(right_ctr) and self._edit_move_wheel == False:
                        self._edit_move_shifter = True
                    elif distance(self.center) < 0.3 and self._edit_move_shifter == False:
                        self._edit_move_wheel = True
                self._edit_last_trigger_press = now
            elif btn_id == openvr.k_EButton_ApplicationMenu and now - self._edit_mode_last_press > 0.2: #B on right
                self._edit_mode_last_press = now
                step = 10
                if self.config.wheel_alpha + step > 100:
                    self.config.wheel_alpha = 0
                else:
                    self.config.wheel_alpha += step

                print("Switch alpha")
                # Switch alpha
                self.wheel_image.set_alpha(self.config.wheel_alpha / 100.0)
            elif btn_id == openvr.k_EButton_A: #A on right
                self.discard_x()
                self.render()
                print("Set x to 0")
            elif btn_id == openvr.k_EButton_Grip and now - self._edit_mode_entry > 0.5:
                self.wheel_image.set_color((1,1,1))
                self.h_shifter_image.set_color((1,1,1))
                self.config.wheel_pitch = int(self.config.wheel_pitch)
                self.is_edit_mode = False
                self.__dict__.pop("_edit_check", None)
        else:
            if self._edit_move_wheel:
                self._edit_move_wheel = False
            if self._edit_move_shifter:
                self._edit_move_shifter = False

        self._edit_last_l_pos = [left_ctr.x, left_ctr.y, left_ctr.z]
        self._edit_last_r_pos = [right_ctr.x, right_ctr.y, right_ctr.z]
        super().edit_mode(left_ctr, right_ctr)
