
from steam_vr_wheel.pyvjoy.vjoydevice import VJoyDevice, HID_USAGE_SL0, HID_USAGE_SL1, HID_USAGE_X, HID_USAGE_Y, HID_USAGE_Z, HID_USAGE_RX, HID_USAGE_RY
import time

def main():
    device = VJoyDevice(1)
    device.ffb_register_gen_cb()
    while True:
        time.sleep(0.2)

if __name__ == "__main__":
    main()