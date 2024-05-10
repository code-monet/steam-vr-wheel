import math
from math import pi, atan2, sin, cos, ceil, sqrt

import openvr
import sys
import numpy as np

if 'DEBUG' in sys.argv:
    DEBUG = True
else:
    DEBUG = False

class Controller:
    def __init__(self, id, name='', vrsys = None, is_controller=True):

        self.id = openvr.TrackedDeviceIndex_t(id)

        self.is_controller = is_controller
        if is_controller:
            self.axis = 0
            self.trackpadX = 0
            self.trackpadY = 0
            self.pressed = 0
        self.x, self.y, self.z = 0, 0, 0
        self.pitch, self.yaw, self.roll = 0, 0, 0
        self.name = name

    def is_pressed(self, btn_id):
        btns = list(reversed(bin(self.pressed)[2:]))
        if len(btns) < btn_id+1 or btns[btn_id] == '0':
            return False
        return True
    
    def update(self, pose):
        vrsys = openvr.VRSystem()

        self.m = pose.mDeviceToAbsoluteTracking
        m = self.m

        self.x = m[0][3]
        self.y = m[1][3]
        self.z = m[2][3]

        R = np.array([[m[0][0], m[0][1], m[0][2]],
                    [m[1][0], m[1][1], m[1][2]],
                    [m[2][0], m[2][1], m[2][2]]])
        #https://learnopencv.com/rotation-matrix-to-euler-angles/
        sy = sqrt(R[0,0] * R[0,0] +  R[1,0] * R[1,0])
        singular = sy < 1e-6
     
        if not singular:
            x = atan2(R[2,1] , R[2,2])
            y = atan2(-R[2,0], sy)
            z = atan2(R[1,0], R[0,0])
        else :
            x = atan2(-R[1,2], R[1,1])
            y = atan2(-R[2,0], sy)
            z = 0
        self.pitch, self.yaw, self.roll = [x/pi*180, y/pi*180, z/pi*180]

        if self.is_controller:
            result, pControllerState = vrsys.getControllerState(self.id)
            self.axis = pControllerState.rAxis[1].x
            self.trackpadX = pControllerState.rAxis[0].x
            self.trackpadY = pControllerState.rAxis[0].y
            self.pressed = pControllerState.ulButtonPressed

        else:
            # Populate normal
            r = np.eye(3)
            r[:] = [[m[0][0], m[0][1], m[0][2]],
                    [m[1][0], m[1][1], m[1][2]],
                    [m[2][0], m[2][1], m[2][2]]]
            p = np.array([self.x, self.y, self.z])
            v = np.array([0, 0, -1])
            r_v = np.dot(r, v)
            self.normal = np.array([r_v[0]+p[0], r_v[1]+p[1], r_v[2]+p[2]])
        
        self.valid = pose.bPoseIsValid
        if DEBUG:
            if self.is_controller:
                print(self.name, "controller axis:")
                for n, i in enumerate(pControllerState.rAxis):
                    print("AXIS", n, "x:", i.x, "y:", i.y)

    def __repr__(self):
        if self.is_controller:
            return '<{} {} Controller position x={}, y={}, z={}, axis={} valid={}>'.format(self.name,
                                                                                       self.id,
                                                                                       self.x,
                                                                                       self.y,
                                                                                       self.z,
                                                                                       self.axis,
                                                                                       self.valid)
        return '<{} {} Device position x={}, y={}, z={}, valid={}>'.format(self.name,
                                                                                       self.id,
                                                                                       self.x,
                                                                                       self.y,
                                                                                       self.z,
                                                                                       self.valid)