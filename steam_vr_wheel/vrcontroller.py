import math
from math import pi, atan2, sin, cos, ceil, sqrt

import time
import openvr
import sys
import numpy as np

if 'DEBUG' in sys.argv:
    DEBUG = True
else:
    DEBUG = False

class Controller:

    @staticmethod
    def set_haptic_intensity(x):
        Controller._haptic_intensity = min(2.0, max(0.0, x))

    _haptic_dict = dict()
    _haptic_intensity = 1.0
    @staticmethod 
    def update_haptic(frames):

        def process_strength(strength, t, f):
            ret = strength
            if callable(strength):
                argc = strength.__code__.co_argcount
                if argc == 1:
                    # Lambda that accepts t 0 to 1
                    ret = strength(t)
                elif argc == 2:
                    # f is total frames count up until now
                    # for frame based pulses
                    ret = strength(t, f)
                else:
                    raise Exception(f"Wrong argc for strength lambda: {argc}")
            elif strength is None:
                ret = 0
            return ret

        now = time.time()

        for py_ctr_id in Controller._haptic_dict:
            start_ds_ary = Controller._haptic_dict[py_ctr_id]
            new_ary = []
            strength_sum = 0
            for start_ds in start_ds_ary:
                start, ds = start_ds
                single_pulse = False
                d_sum = 0 # Duration sum
                ended = True
                for duration, strength in ds:
                    start_at = start + d_sum
                    if duration is None or duration == 0:
                        # Single frame haptic
                        strength_sum += process_strength(strength, start_at, frames)
                        single_pulse = True
                        break

                    # if duration is not None:
                    d_sum += duration
                    if start_at + duration > now:
                        # Still playing haptic
                        t = (now-start_at) / duration
                        
                        strength_sum += process_strength(strength, t, frames)
                        ended = False
                        break

                #
                if single_pulse == True:
                    ds.pop(0)
                    ended = len(ds) == 0
                    
                if ended == False:
                    new_ary.append(start_ds)
            # Remove ended start_ds entries
            Controller._haptic_dict[py_ctr_id] = new_ary

            # Finally play haptic
            strength_sum = min(1, strength_sum)
            strength_sum *= Controller._haptic_intensity
            # Convert the strength to make it feel linear to human
            strength_sum = ((math.exp(strength_sum) - 1) / (math.e - 1))
            if strength_sum > 0:
                openvr.VRSystem().triggerHapticPulse( \
                    openvr.TrackedDeviceIndex_t(py_ctr_id),
                    0,
                    # Use 3000 (3ms or 3000µs) as max strength set here
                    # Since frequency is 60hz, 3ms can fit in each frame
                    int(strength_sum * 3000)) # 3ms

    # Valid ds arguments
    # [1.0, 1.0]
    #     => pulse with strength of 1.0 EVERY FRAME for 1 second
    # [None, 1.0] == [0.0, 1.0]
    #     => SINGLE PULSE with strength of 1.0 SINGLE PULSE means it is for just ONE FRAME
    # [1.0, None] == [1.0, 0.0]
    #     => no haptic for 1 second
    # [2.0, lambda t: t]
    #     => for 2 seconds, pulse increasing from 0 to 1 (t is relative to the total duration)
    # [2.0, lambda t,f: 1 if f%10 == 0 else 0]
    #     => for 2 seconds, pulse of strength 1 every 10 frames
    # [None, lambda t,f: 1 if f%10 == 0 else 0]
    #     => pulse of strength 1 if the current frame is every 10th frame

    def haptic(self, *ds):
        if self.id.value not in Controller._haptic_dict:
            Controller._haptic_dict[self.id.value] = []
        arr = Controller._haptic_dict[self.id.value]
        start = time.time()
        arr.append([start, list(ds)])

    def __init__(self, id, name='', vrsys = None, is_controller=True):

        self.id = openvr.TrackedDeviceIndex_t(id)

        self.is_controller = is_controller
        if is_controller:
            self.axis = 0
            self.axis2 = 0
            self.trackpadX = 0
            self.trackpadY = 0
            self.pressed = 0
            self.touched = 0
        self.x, self.y, self.z = 0, 0, 0
        self.pitch, self.yaw, self.roll = 0, 0, 0
        self.name = name

    def is_pressed(self, btn_id):
        btns = list(reversed(bin(self.pressed)[2:]))
        if len(btns) < btn_id+1 or btns[btn_id] == '0':
            return False
        return True
    
    def is_touched(self, btn_id):
        btns = list(reversed(bin(self.touched)[2:]))
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

            # rAxis[1] = Trigger for Quest 2
            # rAxis[2] = Grip for Quest 2
            self.axis = pControllerState.rAxis[1].x
            self.axis2 = pControllerState.rAxis[2].x
            self.trackpadX = pControllerState.rAxis[0].x
            self.trackpadY = pControllerState.rAxis[0].y
            self.pressed = pControllerState.ulButtonPressed
            self.touched = pControllerState.ulButtonTouched

            '''
k_EButton_A 7   
k_EButton_ApplicationMenu   1   
k_EButton_Axis0 32  
k_EButton_Axis1 33  
k_EButton_Axis2 34  
k_EButton_Axis3 35  
k_EButton_Axis4 36  
k_EButton_Dashboard_Back    2   
k_EButton_DPad_Down 6   
k_EButton_DPad_Left 3   
k_EButton_DPad_Right    5   
k_EButton_DPad_Up   4   
k_EButton_Grip  2   
k_EButton_Knuckles_A    2   
k_EButton_Knuckles_B    1   
k_EButton_Knuckles_JoyStick 35  
k_EButton_Max   64  
k_EButton_ProximitySensor   31  
k_EButton_SteamVR_Touchpad  32  
k_EButton_SteamVR_Trigger   33  
k_EButton_System    0
            '''

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