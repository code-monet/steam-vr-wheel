import json
import os, sys
import threading
import queue
import shutil
import hashlib
import openvr
import copy
from collections import OrderedDict

import time
import numpy as np


class ImageDataDict(dict):
    def __missing__(self, media_path):
        from PIL import Image
        with Image.open(media_path) as img:
            img = img.convert("RGBA")
            width, height = img.size
            depth = 4
            buffer = img.tobytes()
        self[media_path] = [buffer, width, height, depth]
        return self[media_path]
IMAGE_DATA = ImageDataDict()

perf_timings = []
def perf_time(key):
    perf_timings.append([key, time.time()])

# Separate MCI worker into its own thread to ensure all the sounds
# share the same thread context
_mci_command_queue = queue.Queue()
def _mci_worker():
    
    from ctypes import c_buffer, windll
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

    while True:
        command, result_queue = _mci_command_queue.get()
        if command == "quit":
            break
        try:
            result = winCommand(*command)
            result_queue.put([result, None])
        except Exception as e:
            result_queue.put([None, e])

        _mci_command_queue.task_done()
mci_thread = threading.Thread(target=_mci_worker, daemon=True)
mci_thread.start()
#_mci_command_queue.put(("quit", None))
#mci_thread.join()
def playsound(sound, block=True, volume=1.0, stop_alias=None):
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
    from random import random
    from time   import sleep

    def winCommand(*command, get_return=False):
        result_queue = queue.Queue()
        _mci_command_queue.put((command, result_queue))
        if get_return == False:
            return

        result, e = result_queue.get()
        if e is not None:
            raise e
        return result

    if stop_alias is not None:
        winCommand('stop', stop_alias)
        return

    alias = 'playsound_' + str(random())
    winCommand('open "' + sound + '" alias', alias)
    winCommand('set', alias, 'time format milliseconds')
    winCommand('setaudio', alias, 'volume to', str(int(volume * 1000)))
    winCommand('play', alias)#, 'from 0 to', durationInMS.decode())

    if block:
        durationInMS = winCommand('status', alias, 'length', get_return=True)
        sleep(float(durationInMS) / 1000.0)
    else:
        return alias


script_dir = os.path.abspath(os.path.dirname(__file__))
os.chdir(script_dir)
print("Current working directory:", os.getcwd())
DEFAULT_CONFIG_NAME = 'config.json'
CONFIG_DIR = os.path.join(os.getcwd(), "../../configs")
print("Current config directory:", os.path.normpath(CONFIG_DIR))
CONFIG_PATH = os.path.join(CONFIG_DIR, DEFAULT_CONFIG_NAME)
MEDIA_DIR = "media"

# Directory
DEFAULT_CONFIG = OrderedDict([
    ('config_name', DEFAULT_CONFIG_NAME),
    ('trigger_pre_press_button', False),
    ('trigger_press_button', False),
    ('multibutton_trackpad', False),
    ('sfx_volume', 65),
    ('haptic_intensity', 100),
    
    ## Joystick as button
    ('j_l_left_button', False),
    ('j_l_right_button', False),
    ('j_l_up_button', False),
    ('j_l_down_button', False),
    ('j_r_left_button', True),
    ('j_r_right_button', True),
    ('j_r_up_button', True),
    ('j_r_down_button', True),
    ('axis_deadzone', 20),

    # Wheel
    ('wheel_center', [0, -0.4, -0.35]),
    ('wheel_size', 0.48),
    ('wheel_grabbed_by_grip', True),
    ('wheel_grabbed_by_grip_toggle', True),
    ('wheel_degrees', 1440),
    ('wheel_centerforce', 100),
    ('wheel_alpha', 100),
    ('wheel_pitch', 0),
    ('wheel_transparent_center', False),
    ('wheel_ffb', True),
    ('wheel_ffb_haptic', False),

    ## Shifter
    ('shifter_center', [0.25, -0.57, -0.15]),
    ('shifter_degree', 6.0),
    ('shifter_alpha', 100),
    ('shifter_scale', 100),
    ('shifter_sequential', False),
    ('shifter_reverse_orientation', "Bottom Left"),

    ## Bike
    ('bike_center', [0, -0.4, -0.35]),
    ('bike_show_handlebar', True),
    ('bike_show_hands', True),
    ('bike_use_ac_server', False),
    ('bike_max_lean', 60),
    ('bike_max_steer', 12),
    ('bike_throttle_sensitivity', 100),
    ('bike_throttle_decrease_per_sec', 10),
    ('bike_mode', "Absolute"),
    ('bike_handlebar_height', 95),
    ('bike_relative_sensitivity', 100),

    # Advanced
    ('advanced_mode', False),
    ('adv_vjoy_device', 1)
])


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
        try:
            os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        except Exception as e:
            print("Failed to create config dir")
            raise e
        self._write()

    def __init__(self, load_defaults=False):

        if load_defaults:
            self._load_default()
        else:
            try:
                with open(CONFIG_PATH) as f:
                    try:
                        deep_copied = copy.deepcopy(DEFAULT_CONFIG)
                        data = json.load(f)
                        deep_copied.update(data)
                        self._data = deep_copied
                    except json.decoder.JSONDecodeError as e:
                        raise ConfigException(str(e))
                    self.validate_config()
            except FileNotFoundError as e:
                raise e

    def validate_config(self, data=None):
        if data is None:
            data = self._data
        for key, value in DEFAULT_CONFIG.items():
            try:
                if type(value) == float:
                    assert float == type(data[key]) or int == type(data[key])
                else:
                    assert type(data[key]) == type(value)
            except KeyError:
                raise ConfigException("Missing key: {}".format(key))
            except AssertionError:
                raise ConfigException("Wrong type for key: {}:{}".format(key, data[key]))

    def _write(self):
        try:
            with open(CONFIG_PATH, 'x') as f:
                 json.dump(self._data, f, indent=2, sort_keys=False)
        except FileExistsError:
            with open(CONFIG_PATH, 'w') as f:
                 json.dump(self._data, f, indent=2, sort_keys=False)


def make_property(key):
    def getter(self):
        return self._data.get(key)
    def setter(self, value):
        self._data[key] = value
        self._write()
    return property(getter, setter)

for key in DEFAULT_CONFIG.keys():
    setattr(PadConfig, key, make_property(key))