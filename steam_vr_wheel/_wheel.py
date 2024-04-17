from collections import deque
from math import pi, atan2, sin, cos, ceil, sqrt

import numpy as np
import openvr
import os
import copy
import time

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

def rotation_matrix(theta1, theta2, theta3, order='xyz'):
    #https://programming-surgeon.com/en/euler-angle-python-en/
    """
    input
        theta1, theta2, theta3 = rotation angles in rotation order (degrees)
        oreder = rotation order of x,y,z　e.g. XZY rotation -- 'xzy'
    output
        3x3 rotation matrix (numpy array)
    """
    c1 = np.cos(theta1 * np.pi / 180)
    s1 = np.sin(theta1 * np.pi / 180)
    c2 = np.cos(theta2 * np.pi / 180)
    s2 = np.sin(theta2 * np.pi / 180)
    c3 = np.cos(theta3 * np.pi / 180)
    s3 = np.sin(theta3 * np.pi / 180)

    if order == 'xzx':
        matrix=np.array([[c2, -c3*s2, s2*s3],
                         [c1*s2, c1*c2*c3-s1*s3, -c3*s1-c1*c2*s3],
                         [s1*s2, c1*s3+c2*c3*s1, c1*c3-c2*s1*s3]])
    elif order=='xyx':
        matrix=np.array([[c2, s2*s3, c3*s2],
                         [s1*s2, c1*c3-c2*s1*s3, -c1*s3-c2*c3*s1],
                         [-c1*s2, c3*s1+c1*c2*s3, c1*c2*c3-s1*s3]])
    elif order=='yxy':
        matrix=np.array([[c1*c3-c2*s1*s3, s1*s2, c1*s3+c2*c3*s1],
                         [s2*s3, c2, -c3*s2],
                         [-c3*s1-c1*c2*s3, c1*s2, c1*c2*c3-s1*s3]])
    elif order=='yzy':
        matrix=np.array([[c1*c2*c3-s1*s3, -c1*s2, c3*s1+c1*c2*s3],
                         [c3*s2, c2, s2*s3],
                         [-c1*s3-c2*c3*s1, s1*s2, c1*c3-c2*s1*s3]])
    elif order=='zyz':
        matrix=np.array([[c1*c2*c3-s1*s3, -c3*s1-c1*c2*s3, c1*s2],
                         [c1*s3+c2*c3*s1, c1*c3-c2*s1*s3, s1*s2],
                         [-c3*s2, s2*s3, c2]])
    elif order=='zxz':
        matrix=np.array([[c1*c3-c2*s1*s3, -c1*s3-c2*c3*s1, s1*s2],
                         [c3*s1+c1*c2*s3, c1*c2*c3-s1*s3, -c1*s2],
                         [s2*s3, c3*s2, c2]])
    elif order=='xyz':
        matrix=np.array([[c2*c3, -c2*s3, s2],
                         [c1*s3+c3*s1*s2, c1*c3-s1*s2*s3, -c2*s1],
                         [s1*s3-c1*c3*s2, c3*s1+c1*s2*s3, c1*c2]])
    elif order=='xzy':
        matrix=np.array([[c2*c3, -s2, c2*s3],
                         [s1*s3+c1*c3*s2, c1*c2, c1*s2*s3-c3*s1],
                         [c3*s1*s2-c1*s3, c2*s1, c1*c3+s1*s2*s3]])
    elif order=='yxz':
        matrix=np.array([[c1*c3+s1*s2*s3, c3*s1*s2-c1*s3, c2*s1],
                         [c2*s3, c2*c3, -s2],
                         [c1*s2*s3-c3*s1, c1*c3*s2+s1*s3, c1*c2]])
    elif order=='yzx':
        matrix=np.array([[c1*c2, s1*s3-c1*c3*s2, c3*s1+c1*s2*s3],
                         [s2, c2*c3, -c2*s3],
                         [-c2*s1, c1*s3+c3*s1*s2, c1*c3-s1*s2*s3]])
    elif order=='zyx':
        matrix=np.array([[c1*c2, c1*s2*s3-c3*s1, s1*s3+c1*c3*s2],
                         [c2*s1, c1*c3+s1*s2*s3, c3*s1*s2-c1*s3],
                         [-s2, c2*s3, c2*c3]])
    elif order=='zxy':
        matrix=np.array([[c1*c3-s1*s2*s3, -c2*s1, c1*s3+c3*s1*s2],
                         [c3*s1+c1*s2*s3, c1*c2, s1*s3-c1*c3*s2],
                         [-c2*s3, s2, c2*c3]])

    return matrix

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
        hand_size = 0.15

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
        check_result(self.vroverlay.setOverlayAlpha(self.l_ovr, 1))
        check_result(self.vroverlay.setOverlayAlpha(self.l_ovr2, 0)) #!!
        check_result(self.vroverlay.setOverlayAlpha(self.r_ovr, 1))
        check_result(self.vroverlay.setOverlayAlpha(self.r_ovr2, 0)) #!!
        check_result(self.vroverlay.setOverlayWidthInMeters(self.l_ovr, hand_size))
        check_result(self.vroverlay.setOverlayWidthInMeters(self.l_ovr2, hand_size))
        check_result(self.vroverlay.setOverlayWidthInMeters(self.r_ovr, hand_size))
        check_result(self.vroverlay.setOverlayWidthInMeters(self.r_ovr2, hand_size))

        this_dir = os.path.abspath(os.path.dirname(__file__))

        self.l_open_png = os.path.join(this_dir, 'media', 'hand_open_l.png')
        self.r_open_png = os.path.join(this_dir, 'media', 'hand_open_r.png')
        self.l_close_png = os.path.join(this_dir, 'media', 'hand_closed_l.png')
        self.r_close_png = os.path.join(this_dir, 'media', 'hand_closed_r.png')

        check_result(self.vroverlay.setOverlayFromFile(self.l_ovr, self.l_open_png.encode()))
        check_result(self.vroverlay.setOverlayFromFile(self.l_ovr2, self.l_close_png.encode())) #!!
        check_result(self.vroverlay.setOverlayFromFile(self.r_ovr, self.r_open_png.encode()))
        check_result(self.vroverlay.setOverlayFromFile(self.r_ovr2, self.r_close_png.encode())) #!!


        result, transform = self.vroverlay.setOverlayTransformTrackedDeviceRelative(self.l_ovr, self.left_ctr.id)
        result, transform = self.vroverlay.setOverlayTransformTrackedDeviceRelative(self.l_ovr2, self.left_ctr.id)
        result, transform = self.vroverlay.setOverlayTransformTrackedDeviceRelative(self.r_ovr, self.right_ctr.id)
        result, transform = self.vroverlay.setOverlayTransformTrackedDeviceRelative(self.r_ovr2, self.right_ctr.id)

        transform[0][0] = 1.0
        transform[0][1] = 0.0
        transform[0][2] = 0.0
        transform[0][3] = 0

        transform[1][0] = 0.0
        transform[1][1] = 1.0
        transform[1][2] = 0.0
        transform[1][3] = 0

        transform[2][0] = 0.0
        transform[2][1] = 0.0
        transform[2][2] = 1.0
        transform[2][3] = 0

        self.transform = transform

        rotate = initRotationMatrix(0, -pi / 2)
        self.transform = matMul33(rotate, self.transform)

        fn = self.vroverlay.function_table.setOverlayTransformTrackedDeviceRelative
        result = fn(self.l_ovr, self.left_ctr.id, openvr.byref(self.transform))
        result = fn(self.l_ovr2, self.left_ctr.id, openvr.byref(self.transform))
        result = fn(self.r_ovr, self.right_ctr.id, openvr.byref(self.transform))
        result = fn(self.r_ovr2, self.right_ctr.id, openvr.byref(self.transform))

        check_result(result)
        check_result(self.vroverlay.showOverlay(self.l_ovr))
        check_result(self.vroverlay.showOverlay(self.l_ovr2))
        check_result(self.vroverlay.showOverlay(self.r_ovr))
        check_result(self.vroverlay.showOverlay(self.r_ovr2))

    def left_grab(self):
        if not self._handl_closed:
            #self.vroverlay.setOverlayFromFile(self.l_ovr, self.l_close_png.encode())
            self.vroverlay.setOverlayAlpha(self.l_ovr, 0)
            self.vroverlay.setOverlayAlpha(self.l_ovr2, 1)
            self._handl_closed = True

    def left_ungrab(self):
        if self._handl_closed:
            #self.vroverlay.setOverlayFromFile(self.l_ovr, self.l_open_png.encode())
            self.vroverlay.setOverlayAlpha(self.l_ovr, 1)
            self.vroverlay.setOverlayAlpha(self.l_ovr2, 0)
            self._handl_closed = False

    def right_grab(self):
        if not self._handr_closed:
            #self.vroverlay.setOverlayFromFile(self.r_ovr, self.r_close_png.encode())
            self.vroverlay.setOverlayAlpha(self.r_ovr, 0)
            self.vroverlay.setOverlayAlpha(self.r_ovr2, 1)
            self._handr_closed = True

    def right_ungrab(self):
        if self._handr_closed:
            #self.vroverlay.setOverlayFromFile(self.r_ovr, self.r_open_png.encode())
            self.vroverlay.setOverlayAlpha(self.r_ovr, 1)
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
    def __init__(self, x=0.25, y=-0.57, z=-0.15, size=0.07):
        self.vrsys = openvr.VRSystem()
        self.vroverlay = openvr.IVROverlay()

        self.x = x
        self.y = y
        self.z = z
        self.size = size
        self.degree = 15

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
        stick_img = os.path.join(this_dir, 'media', 'h_shifter_stick.png')
        knob_img = os.path.join(this_dir, 'media', 'h_shifter_knob.png')

        check_result(self.vroverlay.setOverlayFromFile(self.slot, slot_img.encode()))
        check_result(self.vroverlay.setOverlayFromFile(self.stick, stick_img.encode()))
        check_result(self.vroverlay.setOverlayFromFile(self.knob, knob_img.encode()))

        # Visibility
        check_result(self.vroverlay.setOverlayColor(self.slot, 1, 1, 1)) # white for the time being
        check_result(self.vroverlay.setOverlayAlpha(self.slot, 1))
        check_result(self.vroverlay.setOverlayWidthInMeters(self.slot, size)) # default 7cm
        
        stick_width = 0.02
        self.stick_width = stick_width
        check_result(self.vroverlay.setOverlayColor(self.stick, 1, 1, 1))
        check_result(self.vroverlay.setOverlayAlpha(self.stick, 0)) # Hide while loading texture
        check_result(self.vroverlay.showOverlay(self.stick)) # Preload texture for dimension checking
        check_result(self.vroverlay.setOverlayWidthInMeters(self.stick, stick_width))

        check_result(self.vroverlay.setOverlayColor(self.knob, 1, 1, 1))
        check_result(self.vroverlay.setOverlayAlpha(self.knob, 1))
        check_result(self.vroverlay.setOverlayWidthInMeters(self.knob, 0.08))

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

        #result, txw, txh = self.vroverlay.getOverlayImageData(self.stick, None, 0)
        txw, txh = 40, 633
        stick_height = txh / (txw / stick_width)
        set_transform(self.stick_tf, [[1.0, 0.0, 0.0, x],
                                    [0.0, 1.0, 0.0, y+stick_height/2],
                                    [0.0, 0.0, 1.0, z]])
        self.stick_height = stick_height

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
        check_result(self.vroverlay.setOverlayAlpha(self.stick, 1)) # Stick
        check_result(self.vroverlay.showOverlay(self.knob))

        # Get HMD id for yaw
        vrsys = openvr.VRSystem()
        for i in range(openvr.k_unMaxTrackedDeviceCount):
            device_class = vrsys.getTrackedDeviceClass(i)
            if device_class == openvr.TrackedDeviceClass_HMD:
                self._hmd_id = i
        poses_t = openvr.TrackedDevicePose_t * openvr.k_unMaxTrackedDeviceCount
        self._poses = poses_t()

        self.last_pos = 3.5

    def get_bounds(self):
        margin = 0.03
        o = self.size/2 + margin
        pmin = (self.x-o, self.y-margin, self.z-o)
        pmax = (self.x+o, self.y+self.stick_height+margin, self.z+o)
        return (pmin, pmax)

    def check_collision(self, ctr):
        x, y, z = ctr.x, ctr.y, ctr.z
        pm, pM = self.get_bounds()
        x0, y0, z0 = pm
        x2, y2, z2 = pM
        
        return x0<=x<=x2 and y0<=y<=y2 and z0<=z<=z2

    def _get_hmd_yaw(self):
        openvr.VRSystem().getDeviceToAbsoluteTrackingPose(openvr.TrackingUniverseSeated, 0, len(self._poses), self._poses)
        m = self._poses[self._hmd_id].mDeviceToAbsoluteTracking
        R = np.array([[m[0][0], m[1][0], m[2][0]],[m[0][1], m[1][1], m[2][1]],[m[0][2], m[1][2], m[2][2]]])
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
        return y/(2*pi)*360

    def set_stick_pos(self, pos):
        """
        |1  |3  |5  |  1 3 5
        |1.5|3.5|5.5|  +-N-+
        |2  |4  |6  |  2 4 6

        odd: towards +z
        x2 is odd: no rotation
        even: towards -z

        x = (round(pos/2)-1) * ...
        z_rot = ((pos%2 if pos%2 != 0 else 2)-1.5) * ...
        """

        # Towards HMD
        yaw = self._get_hmd_yaw()

        offset = (self.size/2 - self.stick_width/2)
        x = self.x + (ceil(pos/2)-2) * offset
        z_fac = ((pos%2 if pos%2 != 0 else 2)-1.5)*2
        z_sin = sin(self.degree*np.pi/180) * self.stick_height

        z_knob = self.z - z_fac * (z_sin + offset)
        z_stick = self.z - z_fac * offset
        rot_knob = rotation_matrix(0, yaw, 0)
        rot_stick = rotation_matrix_around_vec(z_fac * -self.degree,
                            (cos((180-yaw)*pi/180), 0, sin((180-yaw)*pi/180)))
        rot_stick = np.dot(rot_stick, rotation_matrix(0, yaw, 0))
        rot_stick_x = rotation_matrix(z_fac * self.degree, 0, 0) #

        y_knob = self.y + self.stick_height - (abs(z_fac)*((1-cos(self.degree*np.pi/180))*self.stick_height))

        def set_tf_rot(tf, mat):
            for i in range(0, 3):
                for j in range(0, 3):
                    tf[j][i] = mat[i][j]

        self.knob_tf[0][3] = x
        self.knob_tf[1][3] = y_knob
        self.knob_tf[2][3] = z_knob
        set_tf_rot(self.knob_tf, rot_knob)

        offset_stick = -np.dot(rot_stick_x, (0, self.stick_height/2, 0))
        self.stick_tf[0][3] = x + offset_stick[0]
        self.stick_tf[1][3] = self.y - offset_stick[1]
        self.stick_tf[2][3] = z_stick + offset_stick[2]
        set_tf_rot(self.stick_tf, rot_stick)


        if self.last_pos != pos:
            self.last_pos = pos 
            #print(yaw)

        fn = self.vroverlay.function_table.setOverlayTransformAbsolute
        fn(self.stick, openvr.TrackingUniverseSeated, openvr.byref(self.stick_tf))
        fn(self.knob, openvr.TrackingUniverseSeated, openvr.byref(self.knob_tf))



class SteeringWheelImage:
    def __init__(self, x=0, y=-0.4, z=-0.35, size=0.55):
        self.vrsys = openvr.VRSystem()
        self.vroverlay = openvr.IVROverlay()
        result, self.wheel = self.vroverlay.createOverlay('keyiiii'.encode(), 'keyiiii'.encode())
        check_result(result)

        check_result(self.vroverlay.setOverlayColor(self.wheel, 1, 1, 1))
        check_result(self.vroverlay.setOverlayAlpha(self.wheel, 1))
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

    def discard_x(self):
        self.transform[0][3] = 0
        fn = self.vroverlay.function_table.setOverlayTransformAbsolute
        fn(self.wheel, openvr.TrackingUniverseSeated, openvr.byref(self.transform))

    def move(self, point, size):
        self.transform[0][3] = point.x
        self.transform[1][3] = point.y
        self.transform[2][3] = point.z
        print(point.x, point.y, point.z)
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

        # radians per frame last turn speed when wheel was being held, gradually decreases after wheel is released
        self._turn_speed = 0

        self.wheel_image = SteeringWheelImage(x=x, y=y, z=z, size=size)
        self.center = Point(x, y, z)
        self.size = size
        self._grab_started_point = None
        self._wheel_grab_offset = 0

        # for manual grab:
        self._left_controller_grabbed = False
        self._right_controller_grabbed = False

        # for triple grip:
        self._triple_grip_start = 0.0
        self._tg_click_count = 0

        # edit mode
        self._edit_mode_last_press = 0.0
        self._edit_mode_entry = 0.0

        # H Shifter
        self.h_shifter_image = HShifterImage()

    def point_in_holding_bounds(self, point):
        width = 0.10
        a = self.size/2 + width
        b = self.size/2 - width
        if self.config.vertical_wheel:
            x = point.x - self.center.x
            y = point.y - self.center.y
            z = point.z - self.center.z
        else:
            z = point.y - self.center.y
            y = point.x - self.center.x
            x = point.z - self.center.z

        if abs(z) < width:
            distance = (x**2+y**2)**0.5
            if distance < b:
                return False
            if distance < a:
                return True
        else:
            return False


    def unwrap_wheel_angles(self):
        period = 2 * pi
        angle = np.array(self._wheel_angles, dtype=float)
        diff = np.diff(angle)
        diff_to_correct = (diff + period / 2.) % period - period / 2.
        increment = np.cumsum(diff_to_correct - diff)
        angle[1:] += increment
        self._wheel_angles[-1] = angle[-1]

    def wheel_raw_angle(self, point):
        if self.config.vertical_wheel:
            a = float(point.y) - self.center.y
            b = float(point.x) - self.center.x
        else:
            a = float(point.x) - self.center.x
            b = float(point.z) - self.center.z
        angle = atan2(a, b)
        return angle

    def wheel_double_raw_angle(self, left_ctr, right_ctr):
        if self.config.vertical_wheel:
            a = left_ctr.y - right_ctr.y
            b = left_ctr.x - right_ctr.x
        else:
            a = left_ctr.x - right_ctr.x
            b = left_ctr.z - right_ctr.z
        return atan2(a, b)

    def ready_to_unsnap(self, l, r):
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
                self._left_controller_grabbed = False

            if button == openvr.k_EButton_Grip and hand == 'right':
                self._right_controller_grabbed = False

            if self._right_controller_grabbed and self._left_controller_grabbed:
                pass
            else:
                self._snapped = False

    def set_button_press(self, button, hand, left_ctr, right_ctr):
        super().set_button_press(button, hand)

        triple_click_time = 0.7
        grab_haptic_magnitude = 250
        now = time.time()


        if button == openvr.k_EButton_Grip and hand == 'left':

            if self.config.wheel_grabbed_by_grip_toggle:
                self._left_controller_grabbed = True

                # Haptic when grabbing wheel
                openvr.VRSystem().triggerHapticPulse(left_ctr.id, 0, grab_haptic_magnitude)
            else:
                self._left_controller_grabbed = not self._left_controller_grabbed

        if button == openvr.k_EButton_Grip and hand == 'right':
            if self.config.wheel_grabbed_by_grip_toggle:
                self._right_controller_grabbed = True
                
                # Haptic when grabbing wheel
                openvr.VRSystem().triggerHapticPulse(right_ctr.id, 0, grab_haptic_magnitude)
            else:
                self._right_controller_grabbed = not self._right_controller_grabbed

        if self._right_controller_grabbed and self._left_controller_grabbed:
            pass
        else:
            self._snapped = False

        
        # Triple grip
        if button == openvr.k_EButton_Grip:

            # Initial
            if self._tg_click_count == 0:
                self._triple_grip_start = now
                self._tg_click_count += 1
            else:
                elapsed = now - self._triple_grip_start

                def reset_tg():
                    self._tg_click_count = 0
                    self._triple_grip_start = 0.0


                if elapsed > triple_click_time:
                    self._tg_click_count = 0
                    self._triple_grip_start = 0.0
                elif self._tg_click_count == 2 and elapsed <= triple_click_time:
                    openvr.VRSystem().triggerHapticPulse(left_ctr.id, 0, 3000)
                    openvr.VRSystem().triggerHapticPulse(right_ctr.id, 0, 3000)

                    self.config.edit_mode = True
                    self._edit_mode_entry = time.time()

                    self._tg_click_count = 0
                    self._triple_grip_start = 0.0
                else:
                    self._tg_click_count += 1

    def _wheel_update(self, left_ctr, right_ctr):
        if self.config.wheel_grabbed_by_grip:
            left_bound, right_bound = self._left_controller_grabbed, self._right_controller_grabbed
        else: # automatic gripping
            right_bound = self.point_in_holding_bounds(right_ctr)
            left_bound = self.point_in_holding_bounds(left_ctr)
            if self.ready_to_unsnap(left_ctr, right_ctr):
                self._snapped = False

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
            self.wheel_image.rotate(-wheel_angle)
        else:
            self.wheel_image.rotate([-wheel_angle, np.pi / 2], [2, 0])

        # Switch alpha
        self.wheel_image.set_alpha(self.config.wheel_alpha / 100.0)

    def limiter(self, left_ctr, right_ctr):
        if abs(self._wheel_angles[-1])/(2*pi)>(self.config.wheel_degrees / 360)/2:
            self._wheel_angles[-1] = self._wheel_angles[-2]
            openvr.VRSystem().triggerHapticPulse(left_ctr.id, 0, 3000)
            openvr.VRSystem().triggerHapticPulse(right_ctr.id, 0, 3000)


    def render_hands(self):
        if self._snapped:
            self.hands_overlay.left_grab()
            self.hands_overlay.right_grab()
            return
        if self._grab_started_point is None:
            self.hands_overlay.left_ungrab()
            self.hands_overlay.right_ungrab()
            return
        grab_hand_role = self.vrsys.getControllerRoleForTrackedDeviceIndex(self._grab_started_point.id)
        if  grab_hand_role == openvr.TrackedControllerRole_RightHand:
            self.hands_overlay.right_grab()
            self.hands_overlay.left_ungrab()
            return
        if grab_hand_role == openvr.TrackedControllerRole_LeftHand:
            self.hands_overlay.left_grab()
            self.hands_overlay.right_ungrab()
            return


    def _wheel_update_common(self, angle, left_ctr, right_ctr):
        if angle:
            self._wheel_angles.append(angle)

        self.unwrap_wheel_angles()

        self.inertia()
        if (not self._left_controller_grabbed) and (not self._right_controller_grabbed):
            self.center_force()
        self.limiter(left_ctr, right_ctr)
        self.send_to_vjoy()


    def update(self, left_ctr, right_ctr):
        if self.hands_overlay is None:
            self.hands_overlay = HandsImage(left_ctr, right_ctr)
        super().update(left_ctr, right_ctr)

        angle = self._wheel_update(left_ctr, right_ctr)

        self._wheel_update_common(angle, left_ctr, right_ctr)
        if self.config.wheel_show_wheel:
            self.wheel_image.show()
            self.render()
        else:
            self.wheel_image.hide()

        if self.config.wheel_show_hands:
            self.hands_overlay.show()
            self.render_hands()
        else:
            self.hands_overlay.hide()

        # H shifter
        if self.h_shifter_image.check_collision(right_ctr):
            openvr.VRSystem().triggerHapticPulse(right_ctr.id, 0, 500)

        now = time.time()
        self.h_shifter_image.set_stick_pos([1,1.5,2,3,3.5,4,5,5.5,6][round((int(now*1000)%2000)/2000*8)])

    def move_wheel(self, right_ctr, left_ctr):
        self.center = Point(right_ctr.x, right_ctr.y, right_ctr.z)
        self.config.wheel_center = [self.center.x, self.center.y, self.center.z]
        size = ((right_ctr.x-left_ctr.x)**2 +(right_ctr.y-left_ctr.y)**2 + (right_ctr.z-left_ctr.z)**2 )**0.5*2
        self.config.wheel_size = size
        self.size = size
        self.wheel_image.move(self.center, size)



    def edit_mode(self, left_ctr, right_ctr):
        result, state_r = openvr.VRSystem().getControllerState(right_ctr.id)
        now = time.time()

        if self.hands_overlay != None:
            self.hands_overlay.show()
        if self.wheel_image != None:
            self.wheel_image.show()

        # Todo: switch alpha, shows the alpha-applied wheel for a second and after that set alpha to 1
        self.wheel_image.set_color((0,1,0))
        if state_r.ulButtonPressed:
            btn_id = list(reversed(bin(state_r.ulButtonPressed)[2:])).index('1')
            if btn_id == openvr.k_EButton_SteamVR_Trigger:
                self.move_wheel(right_ctr, left_ctr)
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
                self.wheel_image.discard_x()
                print("Set x to 0")
            elif btn_id == openvr.k_EButton_Grip and now - self._edit_mode_entry > 0.5:
                self.wheel_image.set_color((1,1,1))
                self.config.edit_mode = False
        
        super().edit_mode(left_ctr, right_ctr)
