import json
import os, sys
import threading
import shutil
import hashlib
import openvr

import time
import numpy as np

def check_result(result):
    if result:
        error_name = openvr.VROverlay().getOverlayErrorNameFromEnum(result)
        raise Exception("OpenVR Error:", error_name)

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


def playsound(sound, block = True, volume=1.0):
    # Copied from playsound==1.2.2 in order to add volume parameter
    # only the windows version
    '''
    Utilizes windll.winmm. Tested and known to work with MP3 and WAVE on
    Windows 7 with Python 2.7. Probably works with more file formats.
    Probably works on Windows XP thru Windows 10. Probably works with all
    versions of Python.

    Inspired by (but not copied from) Michael Gundlach <gundlach@gmail.com>'s mp3play:
    https://github.com/michaelgundlach/mp3play

    I never would have tried using windll.winmm without seeing his code.
    '''
    from ctypes import c_buffer, windll
    from random import random
    from time   import sleep
    from sys    import getfilesystemencoding

    def winCommand(*command):
        buf = c_buffer(255)
        command = ' '.join(command).encode(getfilesystemencoding())
        errorCode = int(windll.winmm.mciSendStringA(command, buf, 254, 0))
        if errorCode:
            errorBuffer = c_buffer(255)
            windll.winmm.mciGetErrorStringA(errorCode, errorBuffer, 254)
            exceptionMessage = ('\n    Error ' + str(errorCode) + ' for command:'
                                '\n        ' + command.decode() +
                                '\n    ' + errorBuffer.value.decode())
            raise Exception(exceptionMessage)
        return buf.value

    alias = 'playsound_' + str(random())
    winCommand('open "' + sound + '" alias', alias)
    winCommand('set', alias, 'time format milliseconds')
    winCommand('setaudio', alias, 'volume to', str(int(volume * 1000)))
    durationInMS = winCommand('status', alias, 'length')
    winCommand('play', alias, 'from 0 to', durationInMS.decode())

    if block:
        sleep(float(durationInMS) / 1000.0)

def bezier_curve(t, P0, P1, P2, P3):
    return (1-t)**3 * P0 + 3*(1-t)**2 * t * P1 + 3*(1-t) * t**2 * P2 + t**3 * P3

DEFAULT_CONFIG_NAME = 'config.json'
CONFIG_DIR = os.path.expanduser(os.path.join('~', '.steam-vr-wheel'))
CONFIG_PATH = os.path.join(CONFIG_DIR, DEFAULT_CONFIG_NAME)

DEFAULT_CONFIG = dict(config_name=DEFAULT_CONFIG_NAME,

                        trigger_pre_press_button=False, trigger_press_button=False,
                        multibutton_trackpad=False,
                        multibutton_trackpad_center_haptic=False,
                      
                        # Wheel
                        wheel_center=[0, -0.4, -0.35], wheel_size=0.48,
                        wheel_grabbed_by_grip=True,
                        wheel_grabbed_by_grip_toggle=True,
                        wheel_show_wheel=True, wheel_show_hands=True,
                        wheel_degrees=1440, wheel_centerforce=3, wheel_alpha=100,
                        wheel_pitch=0, wheel_transparent_center=False,
                        wheel_adaptive_center=False,
                        wheel_ffb=False,

                        ## Shifter
                        shifter_center=[0.25, -0.57, -0.15], shifter_degree=8, shifter_alpha=100,
                        shifter_scale=100,
                        shifter_adaptive_bounds=False,
                        shifter_reverse_orientation="Bottom Left",

                        ### Joystick as button
                        j_l_left_button=False,
                        j_l_right_button=False,
                        j_l_up_button=False,
                        j_l_down_button=False,
                        j_r_left_button=False,
                        j_r_right_button=False,
                        j_r_up_button=False,
                        j_r_down_button=False,

                        ## Bike
                        bike_center=[0, -0.4, -0.35],
                        bike_show_handlebar=True,
                        bike_show_hands=True,
                        bike_max_lean=60,
                        bike_max_steer=12,
                        bike_angle_deadzone=5,
                        bike_throttle_sensitivity=100,
                        bike_throttle_decrease_per_sec=10,
                        
                        bike_mode="Absolute",

                        bike_handlebar_height=95,
                        bike_bound_hand="Both Hands",

                        bike_relative_sensitivity=100,

                        # Disabled
                        touchpad_always_updates=True, vertical_wheel=True,
                        joystick_updates_only_when_grabbed=False, joystick_grabbing_switch=False,
                        edit_mode=False,
                        )


class ConfigException(Exception):
    pass


def md5_file(path):
    if os.path.exists(path) == False:
        raise Exception("Invalid path")

    md5 = hashlib.md5()
    with open(path, 'rb') as f:
        while True:
            data = f.read(2048)
            if not data:
                break
            md5.update(data)

    return md5.hexdigest()

class PadConfig:

    @staticmethod
    def find_current_profile():
        profiles = __class__.get_profiles()

        md5_0 = md5_file(CONFIG_PATH)

        for p in profiles:
            md5_1 = md5_file(os.path.join(CONFIG_DIR, p))
            if md5_0 == md5_1:
                return p

        return ""

    @staticmethod
    def get_config_dir():
        return CONFIG_DIR

    @staticmethod
    def get_profiles():
        profiles = [
            f for f in os.listdir(CONFIG_DIR)
            if (
                os.path.isfile(os.path.join(CONFIG_DIR, f)) and
                f != DEFAULT_CONFIG_NAME and
                len(f) > 5 and
                f[-5:] == ".json")]
        return profiles

    @staticmethod
    def switch_profile(p):
        new_cfg = os.path.join(CONFIG_DIR, p)
        if os.path.exists(new_cfg) == False:
            raise Exception("Specified config file doesn't exist")

        shutil.copyfile(new_cfg, CONFIG_PATH)

    @staticmethod
    def save_as_new_profile(p):
        shutil.copyfile(CONFIG_PATH, os.path.join(CONFIG_DIR, p))

    @staticmethod
    def __save_as_new_profile():
        profiles = __class__.get_profiles()
        n = "profile-%d.json" % (len(profiles)+1)

        i = 0
        while os.path.exists(os.path.join(CONFIG_DIR, n)):
            i += 1
            n = "profile-%d.json" % i

        shutil.copyfile(CONFIG_PATH, os.path.join(CONFIG_DIR, n))
        return n

    @staticmethod
    def save_to_profile(p):
        shutil.copyfile(CONFIG_PATH, os.path.join(CONFIG_DIR, p))

    @staticmethod
    def delete_profile(p):
        ph = os.path.join(CONFIG_DIR, p)
        if os.path.exists(ph):
            os.remove(ph)

    def _load_default(self):
        self._data = DEFAULT_CONFIG
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        self._write()

    def __init__(self, load_defaults=False):
        if load_defaults:
            self._load_default()
        else:
            try:
                with open(CONFIG_PATH) as f:
                    try:
                        self._data = json.load(f)
                    except json.decoder.JSONDecodeError as e:
                        raise ConfigException(str(e))
                    self.validate_config()
            except FileNotFoundError as e:
                raise ConfigException(str(e))

    def validate_config(self, data=None):
        if data is None:
            data = self._data
        for key, value in DEFAULT_CONFIG.items():
            try:
                assert type(data[key]) == type(value)
            except KeyError:
                raise ConfigException("Missing key: {}".format(key))
            except AssertionError:
                raise ConfigException("Wrong type for key: {}:{}".format(key, data[key]))

    def _write(self):
        try:
            with open(CONFIG_PATH, 'x') as f:
                 json.dump(self._data, f)
        except FileExistsError:
            with open(CONFIG_PATH, 'w') as f:
                 json.dump(self._data, f)

    @property
    def config_name(self):
        return self._data['config_name']

    @config_name.setter
    def config_name(self, x: bool):
        self._data['config_name'] = x
        self._write()

    @property
    def trigger_pre_press_button(self):
        return self._data['trigger_pre_press_button']

    @trigger_pre_press_button.setter
    def trigger_pre_press_button(self, x: bool):
        self._data['trigger_pre_press_button'] = x
        self._write()

    @property
    def trigger_press_button(self):
        return self._data['trigger_press_button']

    @trigger_press_button.setter
    def trigger_press_button(self, x: bool):
        self._data['trigger_press_button'] = x
        self._write()

    @property
    def multibutton_trackpad(self):
        return self._data['multibutton_trackpad']

    @multibutton_trackpad.setter
    def multibutton_trackpad(self, x: bool):
        self._data['multibutton_trackpad'] = x
        self._write()

    @property
    def multibutton_trackpad_center_haptic(self):
        return self._data['multibutton_trackpad_center_haptic']

    @multibutton_trackpad_center_haptic.setter
    def multibutton_trackpad_center_haptic(self, x: bool):
        self._data['multibutton_trackpad_center_haptic'] = x
        self._write()

    @property
    def touchpad_always_updates(self):
        return self._data['touchpad_always_updates']

    @touchpad_always_updates.setter
    def touchpad_always_updates(self, x: bool):
        self._data['touchpad_always_updates'] = x
        self._write()

    @property
    def vertical_wheel(self):
        return self._data['vertical_wheel']

    @vertical_wheel.setter
    def vertical_wheel(self, x: bool):
        self._data['vertical_wheel'] = x
        self._write()

    @property
    def joystick_updates_only_when_grabbed(self):
        return self._data['joystick_updates_only_when_grabbed']

    @joystick_updates_only_when_grabbed.setter
    def joystick_updates_only_when_grabbed(self, x: bool):
        self._data['joystick_updates_only_when_grabbed'] = x
        self._write()

    @property
    def joystick_grabbing_switch(self):
        return self._data['joystick_grabbing_switch']

    @joystick_grabbing_switch.setter
    def joystick_grabbing_switch(self, x: bool):
        self._data['joystick_grabbing_switch'] = x
        self._write()

    @property
    def edit_mode(self):
        return self._data['edit_mode']

    @edit_mode.setter
    def edit_mode(self, x: bool):
        self._data['edit_mode'] = x
        self._write()

    @property
    def wheel_center(self):
        return self._data['wheel_center']

    @wheel_center.setter
    def wheel_center(self, x: bool):
        self._data['wheel_center'] = x
        self._write()

    @property
    def wheel_size(self):
        return self._data['wheel_size']

    @wheel_size.setter
    def wheel_size(self, x: bool):
        self._data['wheel_size'] = x
        self._write()

    @property
    def wheel_grabbed_by_grip(self):
        return self._data['wheel_grabbed_by_grip']

    @wheel_grabbed_by_grip.setter
    def wheel_grabbed_by_grip(self, x: bool):
        self._data['wheel_grabbed_by_grip'] = x
        self._write()

    @property
    def wheel_grabbed_by_grip_toggle(self):
        return self._data['wheel_grabbed_by_grip_toggle']

    @wheel_grabbed_by_grip_toggle.setter
    def wheel_grabbed_by_grip_toggle(self, x: bool):
        self._data['wheel_grabbed_by_grip_toggle'] = x
        self._write()

    @property
    def wheel_degrees(self):
        return self._data['wheel_degrees']

    @wheel_degrees.setter
    def wheel_degrees(self, x: int):
        self._data['wheel_degrees'] = x
        self._write()

    @property
    def wheel_centerforce(self):
        return self._data['wheel_centerforce']

    @wheel_centerforce.setter
    def wheel_centerforce(self, x: int):
        self._data['wheel_centerforce'] = x
        self._write()

    @property
    def wheel_alpha(self):
        return self._data['wheel_alpha']

    @wheel_alpha.setter
    def wheel_alpha(self, x: int):
        self._data['wheel_alpha'] = x
        self._write()

    @property
    def wheel_pitch(self):
        return self._data['wheel_pitch']

    @wheel_pitch.setter
    def wheel_pitch(self, x: int):
        self._data['wheel_pitch'] = x
        self._write()

    @property
    def wheel_transparent_center(self):
        return self._data['wheel_transparent_center']

    @wheel_transparent_center.setter
    def wheel_transparent_center(self, x: bool):
        self._data['wheel_transparent_center'] = x
        self._write()

    @property
    def wheel_adaptive_center(self):
        return self._data['wheel_adaptive_center']

    @wheel_adaptive_center.setter
    def wheel_adaptive_center(self, x: bool):
        self._data['wheel_adaptive_center'] = x
        self._write()

    @property
    def wheel_ffb(self):
        return self._data['wheel_ffb']

    @wheel_ffb.setter
    def wheel_ffb(self, x: bool):
        self._data['wheel_ffb'] = x
        self._write()

    @property
    def wheel_show_wheel(self):
        return self._data['wheel_show_wheel']

    @wheel_show_wheel.setter
    def wheel_show_wheel(self, x: bool):
        self._data['wheel_show_wheel'] = x
        self._write()

    @property
    def wheel_show_hands(self):
        return self._data['wheel_show_hands']

    @wheel_show_hands.setter
    def wheel_show_hands(self, x: bool):
        self._data['wheel_show_hands'] = x
        self._write()

    # Shifter
    @property
    def shifter_center(self):
        return self._data['shifter_center']

    @shifter_center.setter
    def shifter_center(self, x: bool):
        self._data['shifter_center'] = x
        self._write()

    @property
    def shifter_degree(self):
        return self._data['shifter_degree']

    @shifter_degree.setter
    def shifter_degree(self, x: int):
        self._data['shifter_degree'] = x
        self._write()

    @property
    def shifter_alpha(self):
        return self._data['shifter_alpha']

    @shifter_alpha.setter
    def shifter_alpha(self, x: int):
        self._data['shifter_alpha'] = x
        self._write()

    @property
    def shifter_scale(self):
        return self._data['shifter_scale']

    @shifter_scale.setter
    def shifter_scale(self, x: int):
        self._data['shifter_scale'] = x
        self._write()

    @property
    def shifter_adaptive_bounds(self):
        return self._data['shifter_adaptive_bounds']

    @shifter_adaptive_bounds.setter
    def shifter_adaptive_bounds(self, x: bool):
        self._data['shifter_adaptive_bounds'] = x
        self._write()

    @property
    def shifter_reverse_orientation(self):
        return self._data['shifter_reverse_orientation']

    @shifter_reverse_orientation.setter
    def shifter_reverse_orientation(self, x: bool):
        self._data['shifter_reverse_orientation'] = x
        self._write()

    # Joystick as button
    @property
    def j_l_left_button(self):
        return self._data['j_l_left_button']

    @j_l_left_button.setter
    def j_l_left_button(self, x: bool):
        self._data['j_l_left_button'] = x
        self._write()

    @property
    def j_l_right_button(self):
        return self._data['j_l_right_button']

    @j_l_right_button.setter
    def j_l_right_button(self, x: bool):
        self._data['j_l_right_button'] = x
        self._write()

    @property
    def j_l_up_button(self):
        return self._data['j_l_up_button']

    @j_l_up_button.setter
    def j_l_up_button(self, x: bool):
        self._data['j_l_up_button'] = x
        self._write()

    @property
    def j_l_down_button(self):
        return self._data['j_l_down_button']

    @j_l_down_button.setter
    def j_l_down_button(self, x: bool):
        self._data['j_l_down_button'] = x
        self._write()

    @property
    def j_r_left_button(self):
        return self._data['j_r_left_button']

    @j_r_left_button.setter
    def j_r_left_button(self, x: bool):
        self._data['j_r_left_button'] = x
        self._write()

    @property
    def j_r_right_button(self):
        return self._data['j_r_right_button']

    @j_r_right_button.setter
    def j_r_right_button(self, x: bool):
        self._data['j_r_right_button'] = x
        self._write()

    @property
    def j_r_up_button(self):
        return self._data['j_r_up_button']

    @j_r_up_button.setter
    def j_r_up_button(self, x: bool):
        self._data['j_r_up_button'] = x
        self._write()

    @property
    def j_r_down_button(self):
        return self._data['j_r_down_button']

    @j_r_down_button.setter
    def j_r_down_button(self, x: bool):
        self._data['j_r_down_button'] = x
        self._write()

    # Bike
    @property
    def bike_show_handlebar(self):
        return self._data['bike_show_handlebar']

    @bike_show_handlebar.setter
    def bike_show_handlebar(self, x: bool):
        self._data['bike_show_handlebar'] = x
        self._write()

    @property
    def bike_show_hands(self):
        return self._data['bike_show_hands']

    @bike_show_hands.setter
    def bike_show_hands(self, x: bool):
        self._data['bike_show_hands'] = x
        self._write()

    @property
    def bike_handlebar_height(self):
        return self._data['bike_handlebar_height']

    @bike_handlebar_height.setter
    def bike_handlebar_height(self, x: int):
        self._data['bike_handlebar_height'] = x
        self._write()

    @property
    def bike_max_lean(self):
        return self._data['bike_max_lean']

    @bike_max_lean.setter
    def bike_max_lean(self, x: int):
        self._data['bike_max_lean'] = x
        self._write()

    @property
    def bike_max_steer(self):
        return self._data['bike_max_steer']

    @bike_max_steer.setter
    def bike_max_steer(self, x: int):
        self._data['bike_max_steer'] = x
        self._write()

    @property
    def bike_angle_deadzone(self):
        return self._data['bike_angle_deadzone']

    @bike_angle_deadzone.setter
    def bike_angle_deadzone(self, x: int):
        self._data['bike_angle_deadzone'] = x
        self._write()

    @property
    def bike_center(self):
        return self._data['bike_center']

    @bike_center.setter
    def bike_center(self, x: bool):
        self._data['bike_center'] = x
        self._write()

    @property
    def bike_mode(self):
        return self._data['bike_mode']

    @bike_mode.setter
    def bike_mode(self, x: bool):
        self._data['bike_mode'] = x
        self._write()

    @property
    def bike_throttle_sensitivity(self):
        return self._data['bike_throttle_sensitivity']

    @bike_throttle_sensitivity.setter
    def bike_throttle_sensitivity(self, x: int):
        self._data['bike_throttle_sensitivity'] = x
        self._write()

    @property
    def bike_throttle_decrease_per_sec(self):
        return self._data['bike_throttle_decrease_per_sec']

    @bike_throttle_decrease_per_sec.setter
    def bike_throttle_decrease_per_sec(self, x: int):
        self._data['bike_throttle_decrease_per_sec'] = x
        self._write()

    @property
    def bike_bound_hand(self):
        return self._data['bike_bound_hand']

    @bike_bound_hand.setter
    def bike_bound_hand(self, x: bool):
        self._data['bike_bound_hand'] = x
        self._write()

    @property
    def bike_relative_sensitivity(self):
        return self._data['bike_relative_sensitivity']

    @bike_relative_sensitivity.setter
    def bike_relative_sensitivity(self, x: bool):
        self._data['bike_relative_sensitivity'] = x
        self._write()
