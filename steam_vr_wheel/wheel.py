import os
import random
import threading
import time

import openvr
import sys

main_done = False

def wheel_main_done():
    global main_done
    return main_done

from . import perf_timings, perf_time
from steam_vr_wheel._bike import Bike
from steam_vr_wheel._virtualpad import VirtualPad
from steam_vr_wheel._wheel import Wheel
from steam_vr_wheel.vrcontroller import Controller
from steam_vr_wheel.configurator import run

FREQUENCY = 60

if 'DEBUG' in sys.argv:
    DEBUG = True
    FREQUENCY = 1
else:
    DEBUG = False



def get_chaperone():

    vrchp_setup = openvr.VRChaperoneSetup()
    _, chp = vrchp_setup.getWorkingSeatedZeroPoseToRawTrackingPose()

    return chp

def do_work(vrsystem, frames, left_ctr: Controller, right_ctr: Controller, hmd: Controller, wheel: Wheel, poses):

    vrsystem.getDeviceToAbsoluteTrackingPose(openvr.TrackingUniverseSeated, 0, len(poses), poses)

    hmd.update(poses[hmd.id.value])
    left_ctr.update(poses[left_ctr.id.value])
    right_ctr.update(poses[right_ctr.id.value])

    event = openvr.VREvent_t()
    while vrsystem.pollNextEvent(event):
        hand = None

        if event.eventType == openvr.VREvent_ChaperoneUniverseHasChanged:
            wheel.update_chaperone(get_chaperone())

            # no pitch and roll
            # https://github.com/ValveSoftware/openvr/issues/905

            #vrchp_setup.function_table.setWorkingSeatedZeroPoseToRawTrackingPose(byref(chp))
            #vrchp_setup.commitWorkingCopy(openvr.EChaperoneConfigFile_Live)

        if event.trackedDeviceIndex == left_ctr.id.value:

            if event.eventType == openvr.VREvent_ButtonTouch:
                if DEBUG:
                    print("LEFT HAND EVENT: BUTTON TOUCH, BUTTON ID", event.data.controller.button)
                if event.data.controller.button == openvr.k_EButton_SteamVR_Touchpad:
                    wheel.set_trackpad_touch_left()
                elif  event.data.controller.button == openvr.k_EButton_SteamVR_Trigger:
                    wheel.set_trigger_touch_left()
            elif  event.eventType == openvr.VREvent_ButtonUntouch:
                if DEBUG:
                    print("LEFT HAND EVENT: BUTTON UNTOUCH, BUTTON ID", event.data.controller.button)
                if event.data.controller.button == openvr.k_EButton_SteamVR_Touchpad:
                    wheel.set_trackpad_untouch_left()
                elif  event.data.controller.button == openvr.k_EButton_SteamVR_Trigger:
                    wheel.set_trigger_untouch_left()

            hand = 'left'
        if event.trackedDeviceIndex == right_ctr.id.value:

            if event.eventType == openvr.VREvent_ButtonTouch:
                if DEBUG:
                    print("RIGHT HAND EVENT: BUTTON TOUCH, BUTTON ID", event.data.controller.button)
                if event.data.controller.button == openvr.k_EButton_SteamVR_Touchpad:
                    wheel.set_trackpad_touch_right()
                elif  event.data.controller.button == openvr.k_EButton_SteamVR_Trigger:
                    wheel.set_trigger_touch_right()
            elif  event.eventType == openvr.VREvent_ButtonUntouch:
                if DEBUG:
                    print("RIGHT HAND EVENT: BUTTON UNTOUCH, BUTTON ID", event.data.controller.button)

                if event.data.controller.button == openvr.k_EButton_SteamVR_Touchpad:
                    wheel.set_trackpad_untouch_right()
                elif  event.data.controller.button == openvr.k_EButton_SteamVR_Trigger:
                    wheel.set_trigger_untouch_right()

            hand = 'right'
        if hand:
            if event.eventType == openvr.VREvent_ButtonPress:
                if DEBUG:
                    print(hand, "HAND EVENT: BUTTON PRESS, BUTTON ID", event.data.controller.button)
                button = event.data.controller.button
                wheel.set_button_press(button, hand, left_ctr, right_ctr)
            if event.eventType == openvr.VREvent_ButtonUnpress:
                if DEBUG:
                    print(hand, "HAND EVENT: BUTTON UNPRESS, BUTTON ID", event.data.controller.button)
                button = event.data.controller.button
                wheel.set_button_unpress(button, hand)
    perf_time("openvr event poll")

    if wheel.is_edit_mode:
        wheel.edit_mode(frames)
    else:
        wheel.update(left_ctr, right_ctr, hmd)


def get_controller_ids():
    vrsys = openvr.VRSystem()
    for i in range(openvr.k_unMaxTrackedDeviceCount):
        device_class = vrsys.getTrackedDeviceClass(i)
        if device_class == openvr.TrackedDeviceClass_Controller:
            role = vrsys.getControllerRoleForTrackedDeviceIndex(i)
            if role == openvr.TrackedControllerRole_RightHand:
                 right = i
            if role == openvr.TrackedControllerRole_LeftHand:
                 left = i

        elif device_class == openvr.TrackedDeviceClass_HMD:
            hmd = i
    return hmd, left, right


def main(type='wheel'):
    openvr.init(openvr.VRApplication_Overlay)
    vrsystem = openvr.VRSystem()
    hands_got = False

    while not hands_got:
        try:
            print('Searching for left and right hand controllers')
            hmd_id, left_ctr_id, right_ctr_id = get_controller_ids()
            hands_got = True
            print('left and right hands found')
        except NameError:
            pass
        time.sleep(0.2)

    hmd       = Controller(hmd_id, name='hmd', vrsys=vrsystem, is_controller=False)
    left_ctr  = Controller(left_ctr_id, name='left', vrsys=vrsystem)
    right_ctr = Controller(right_ctr_id, name='right', vrsys=vrsystem)
    if type == 'wheel':
        wheel = Wheel()
    elif type == 'bike':
        wheel = Bike()
    elif type == 'pad':
        wheel = VirtualPad()

    # Pre loop
    wheel.hmd = hmd
    wheel.left_ctr = left_ctr
    wheel.right_ctr = right_ctr
    wheel.update_chaperone(get_chaperone())
    print("""
---------------------

Required vJoy version: v2.1.9.1
Open Configure vJoy
    - Select vJoy device 1
    - Number of buttons  :   64
    - Axes               :   all enabled
    - POVs               :   Continuous 0
    - Force Feedback     :   Enable Effects and check all

Triple grips both hands     -     enter edit mode

---------------------
    """)

    poses_t = openvr.TrackedDevicePose_t * openvr.k_unMaxTrackedDeviceCount
    poses = poses_t()

    # Loop
    frames = 0
    while True:

        frames += 1
        
        before_work = time.time()

        perf_timings.clear()
        do_work(vrsystem, frames, left_ctr, right_ctr, hmd, wheel, poses)
        Controller.update_haptic(frames)

        after_work = time.time()

        left = 1/FREQUENCY - (after_work - before_work)
        if left > 0:
            time.sleep(left)
        else:
            print(f"Task took too long +{round((-left)/(1/FREQUENCY), 1)} frames")
            for key, t in perf_timings:
                d = t - before_work
                print(f"- +{d:.6f}: {key}")
            print("")

if __name__ == '__main__':
    try:
        main()
    except:
        main_done = True
