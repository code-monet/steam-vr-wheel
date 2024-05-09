import sys
import wx
import os

from steam_vr_wheel import PadConfig, ConfigException

def _decrease_font(w):
    f = w.GetFont()
    p = f.GetPointSize()
    f.SetPointSize(p-1)
    w.SetFont(f)
    return w

class ConfiguratorApp:
    def __init__(self):

        self.app = wx.App()
        self.window = wx.Frame(None, title="steam-vr-wheel Configuration", style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.MINIMIZE_BOX ^ wx.MAXIMIZE_BOX)
        self.parent_pnl = wx.Panel(self.window)
        self.parent_hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.pnl = wx.Panel(self.parent_pnl)
        self.vbox = wx.BoxSizer(wx.VERTICAL)

        #
        self.pnl_profile_buttons = wx.Panel(self.pnl)
        self.hbox_profile_buttons = wx.BoxSizer(wx.HORIZONTAL)
        self.profile_combo = wx.ComboBox(self.pnl_profile_buttons, style=wx.CB_READONLY, size=(160,24))
        self.profile_new = wx.Button(self.pnl_profile_buttons, label="New", size=(60,22))
        self.profile_delete = wx.Button(self.pnl_profile_buttons, label="Delete", size=(60,22))
        self.profile_open_dir = wx.Button(self.pnl_profile_buttons, label="Open", size=(60,22))

        #
        self.trigger_pre_btn_box = wx.CheckBox(self.pnl, label='Button click when resting finger on triggers (button 31, 32)')
        self.trigger_btn_box = wx.CheckBox(self.pnl, label='Button click when pressing triggers (button 1, 9)')
        self.multibutton_trackpad_box = wx.CheckBox(self.pnl, label='(VIVE) Trackpad clicks has 4 additional zones')
        self.multibutton_trackpad_center_haptic_box = wx.CheckBox(self.pnl,
                                                                  label='(VIVE) Haptic feedback for trackpad button zones')
        
        ### hidden
        self.touchpad_always_updates_box = wx.CheckBox(self.pnl, label='Touchpad mapping to axis while untouched (axis move to center when released)')
        self.touchpad_always_updates_box.Hide()
        self.vertical_wheel_box = wx.CheckBox(self.pnl, label='Steering wheel is vertical')
        self.vertical_wheel_box.Hide()
        self.joystick_updates_only_when_grabbed_box = wx.CheckBox(self.pnl, label='Joystick moves only when grabbed (by right grip)')
        self.joystick_updates_only_when_grabbed_box.Hide()
        self.joystick_grabbing_switch_box = wx.CheckBox(self.pnl, label='Joystick grab is a switch')
        self.joystick_grabbing_switch_box.Hide()
        self.edit_mode_box = wx.CheckBox(self.pnl, label='Layout edit mode')
        self.edit_mode_box.Hide()
        ###

        self.wheel_grabbed_by_grip_box = wx.CheckBox(self.pnl, label='Manual wheel grabbing')
        self.wheel_grabbed_by_grip_box_toggle = wx.CheckBox(self.pnl, label='Grabbing object is NOT toggle')
        self.wheel_show_wheel = wx.CheckBox(self.pnl, label="Show Wheel Overlay")
        self.wheel_show_wheel.Disable()
        self.wheel_show_hands = wx.CheckBox(self.pnl, label="Show Hands Overlay")
        self.wheel_show_hands.Disable()
        self.wheel_degrees = wx.SpinCtrl(self.pnl, name = "Wheel Degrees", max = 10000)
        self.wheel_centerforce = wx.SpinCtrl(self.pnl, name = "Center Force")
        self.wheel_ffb = wx.CheckBox(self.pnl, label="Enable Force Feedback (test)")
        self.wheel_ffb.Disable()
        self.wheel_pitch = wx.SpinCtrl(self.pnl, name = "Wheel Pitch", min=-30, max=120)
        self.wheel_alpha = wx.SpinCtrl(self.pnl, name = "Wheel Alpha", max = 100)
        self.wheel_transparent_center_box = wx.CheckBox(self.pnl, label='Wheel becomes transparent while looking at it')
        self.wheel_adaptive_center_box = wx.CheckBox(self.pnl, label='Wheel moves in order to prevent abrupt turn (experimental)')

        # Shifter
        self.pnl_shifter = wx.Panel(self.pnl)
        self.hbox_shifter = wx.BoxSizer(wx.HORIZONTAL)

        self.pnl_shifter_degree = wx.Panel(self.pnl_shifter)
        self.vbox_shifter_degree = wx.BoxSizer(wx.VERTICAL)
        self.shifter_degree = wx.SpinCtrl(self.pnl_shifter_degree, name = "Shifter Degree, 15deg", min=0, max=90)

        self.pnl_shifter_alpha = wx.Panel(self.pnl_shifter)
        self.vbox_shifter_alpha = wx.BoxSizer(wx.VERTICAL)
        self.shifter_alpha = wx.SpinCtrl(self.pnl_shifter_alpha, name = "Shifter Alpha (%), 100%", min=0, max=100)
        
        self.pnl_shifter_scale = wx.Panel(self.pnl_shifter)
        self.vbox_shifter_scale = wx.BoxSizer(wx.VERTICAL)
        self.shifter_scale = wx.SpinCtrl(self.pnl_shifter_scale, name = "Shifter Height Scale (%), 100%", min=10, max=100)
        
        self.shifter_adaptive_bounds_box = wx.CheckBox(self.pnl, label='You need to grab where the shifter exactly is')

        self.shifter_reverse_orientation = wx.RadioBox(self.pnl, label="Reverse Position",
            choices=["Top Left", "Bottom Left", "Top Right", "Bottom Right"],
            majorDimension=1, style=wx.RA_SPECIFY_ROWS)

        # Joystick button or axis
        self.pnl_joystick = wx.Panel(self.pnl)
        self.hbox_joystick = wx.BoxSizer(wx.HORIZONTAL)
        self.j_l_left_button = wx.CheckBox(self.pnl_joystick, label='L ◀')
        self.j_l_right_button = wx.CheckBox(self.pnl_joystick, label='L ▶')
        self.j_l_up_button = wx.CheckBox(self.pnl_joystick, label='L ▲')
        self.j_l_down_button = wx.CheckBox(self.pnl_joystick, label='L ▼')
        self.j_r_left_button = wx.CheckBox(self.pnl_joystick, label='R ◀')
        self.j_r_right_button = wx.CheckBox(self.pnl_joystick, label='R ▶')
        self.j_r_up_button = wx.CheckBox(self.pnl_joystick, label='R ▲')
        self.j_r_down_button = wx.CheckBox(self.pnl_joystick, label='R ▼')

        # BINDINGS
        # Profile binds
        self.profile_combo.Bind(wx.EVT_COMBOBOX, self.profile_change)
        self.profile_new.Bind(wx.EVT_BUTTON, self.profile_buttons)
        self.profile_delete.Bind(wx.EVT_BUTTON, self.profile_buttons)
        self.profile_open_dir.Bind(wx.EVT_BUTTON, self.profile_buttons)

        #
        self.trigger_pre_btn_box.Bind(wx.EVT_CHECKBOX, self.config_change)
        self.trigger_btn_box.Bind(wx.EVT_CHECKBOX, self.config_change)
        self.multibutton_trackpad_box.Bind(wx.EVT_CHECKBOX, self.config_change)
        self.multibutton_trackpad_center_haptic_box.Bind(wx.EVT_CHECKBOX, self.config_change)
        self.touchpad_always_updates_box.Bind(wx.EVT_CHECKBOX, self.config_change)
        self.vertical_wheel_box.Bind(wx.EVT_CHECKBOX, self.config_change)
        self.joystick_updates_only_when_grabbed_box.Bind(wx.EVT_CHECKBOX, self.config_change)
        self.joystick_grabbing_switch_box.Bind(wx.EVT_CHECKBOX, self.config_change)
        self.edit_mode_box.Bind(wx.EVT_CHECKBOX, self.config_change)
        self.wheel_grabbed_by_grip_box.Bind(wx.EVT_CHECKBOX, self.config_change)
        self.wheel_grabbed_by_grip_box_toggle.Bind(wx.EVT_CHECKBOX, self.config_change)
        self.wheel_show_wheel.Bind(wx.EVT_CHECKBOX, self.config_change)
        self.wheel_show_hands.Bind(wx.EVT_CHECKBOX, self.config_change)
        self.wheel_degrees.Bind(wx.EVT_SPINCTRL, self.config_change)
        self.wheel_centerforce.Bind(wx.EVT_SPINCTRL, self.config_change)
        self.wheel_pitch.Bind(wx.EVT_SPINCTRL, self.config_change)
        self.wheel_alpha.Bind(wx.EVT_SPINCTRL, self.config_change)
        self.wheel_transparent_center_box.Bind(wx.EVT_CHECKBOX, self.config_change)
        self.wheel_adaptive_center_box.Bind(wx.EVT_CHECKBOX, self.config_change)

        # Shifter
        self.shifter_degree.Bind(wx.EVT_SPINCTRL, self.config_change)
        self.shifter_alpha.Bind(wx.EVT_SPINCTRL, self.config_change)
        self.shifter_scale.Bind(wx.EVT_SPINCTRL, self.config_change)
        self.shifter_adaptive_bounds_box.Bind(wx.EVT_CHECKBOX, self.config_change)
        self.shifter_reverse_orientation.Bind(wx.EVT_RADIOBOX, self.config_change)

        # Joystick button or axis
        self.j_l_left_button.Bind(wx.EVT_CHECKBOX, self.config_change)
        self.j_l_right_button.Bind(wx.EVT_CHECKBOX, self.config_change)
        self.j_l_up_button.Bind(wx.EVT_CHECKBOX, self.config_change)
        self.j_l_down_button.Bind(wx.EVT_CHECKBOX, self.config_change)
        self.j_r_left_button.Bind(wx.EVT_CHECKBOX, self.config_change)
        self.j_r_right_button.Bind(wx.EVT_CHECKBOX, self.config_change)
        self.j_r_up_button.Bind(wx.EVT_CHECKBOX, self.config_change)
        self.j_r_down_button.Bind(wx.EVT_CHECKBOX, self.config_change)

        self._config_map = dict(trigger_pre_press_button=self.trigger_pre_btn_box,
                                trigger_press_button=self.trigger_btn_box,
                                multibutton_trackpad=self.multibutton_trackpad_box,
                                multibutton_trackpad_center_haptic=self.multibutton_trackpad_center_haptic_box,
                                touchpad_always_updates=self.touchpad_always_updates_box,
                                vertical_wheel=self.vertical_wheel_box,
                                joystick_updates_only_when_grabbed=self.joystick_updates_only_when_grabbed_box,
                                joystick_grabbing_switch=self.joystick_grabbing_switch_box,
                                edit_mode=self.edit_mode_box,
                                wheel_grabbed_by_grip=self.wheel_grabbed_by_grip_box,
                                wheel_grabbed_by_grip_toggle=self.wheel_grabbed_by_grip_box_toggle,
                                wheel_show_wheel=self.wheel_show_wheel,
                                wheel_show_hands=self.wheel_show_hands,
                                wheel_degrees=self.wheel_degrees,
                                wheel_centerforce=self.wheel_centerforce,
                                wheel_ffb=self.wheel_ffb,
                                wheel_pitch=self.wheel_pitch,
                                wheel_alpha=self.wheel_alpha,
                                wheel_transparent_center=self.wheel_transparent_center_box,
                                wheel_adaptive_center=self.wheel_adaptive_center_box,

                                shifter_degree=self.shifter_degree,
                                shifter_alpha=self.shifter_alpha,
                                shifter_scale=self.shifter_scale,
                                shifter_adaptive_bounds=self.shifter_adaptive_bounds_box,
                                shifter_reverse_orientation=self.shifter_reverse_orientation,

                                j_l_left_button=self.j_l_left_button,
                                j_l_right_button=self.j_l_right_button,
                                j_l_up_button=self.j_l_up_button,
                                j_l_down_button=self.j_l_down_button,
                                j_r_left_button=self.j_r_left_button,
                                j_r_right_button=self.j_r_right_button,
                                j_r_up_button=self.j_r_up_button,
                                j_r_down_button=self.j_r_down_button,
                                )

        self.vbox.AddSpacer(5)

        self.vbox.Add(wx.StaticText(self.pnl, label = "Selected Profile"))
        self.hbox_profile_buttons.Add(self.profile_combo)
        self.hbox_profile_buttons.AddSpacer(6)
        self.hbox_profile_buttons.Add(self.profile_new)
        self.hbox_profile_buttons.Add(self.profile_delete)
        self.hbox_profile_buttons.Add(self.profile_open_dir)
        self.pnl_profile_buttons.SetSizerAndFit(self.hbox_profile_buttons)
        self.vbox.Add(self.pnl_profile_buttons)
        self.vbox.AddSpacer(12)

        self.vbox.Add(self.trigger_pre_btn_box)
        self.vbox.Add(self.trigger_btn_box)
        self.vbox.Add(self.multibutton_trackpad_box)
        self.vbox.Add(_decrease_font(
            wx.StaticText(self.pnl, label = " Trackpads have 4 more button ids depending on the clicked zone\n Quest 2 is recommended to uncheck")))
        self.vbox.Add(self.multibutton_trackpad_center_haptic_box)
        self.vbox.Add(_decrease_font(
            wx.StaticText(self.pnl, label = " Haptic feedback when you click on a different click zone\n Quest 2 is recommended to uncheck")))
        self.vbox.Add(self.touchpad_always_updates_box)
        self.vbox.Add(self.vertical_wheel_box)
        self.vbox.Add(self.joystick_updates_only_when_grabbed_box)
        self.vbox.Add(self.joystick_grabbing_switch_box)
        self.vbox.Add(self.edit_mode_box)
        self.vbox.Add(self.wheel_grabbed_by_grip_box)
        self.vbox.Add(self.wheel_grabbed_by_grip_box_toggle)
        self.vbox.Add(self.wheel_show_wheel)
        self.vbox.Add(self.wheel_show_hands)
        self.vbox.AddSpacer(10)
        self.vbox.Add(wx.StaticText(self.pnl, label = "Wheel Degrees"))
        self.vbox.Add(_decrease_font(
            wx.StaticText(self.pnl, label = "360=F1 540 - 1080=Rally car 1440=Default 900 - 1800=Truck")))
        self.vbox.Add(self.wheel_degrees)
        self.vbox.AddSpacer(4)
        self.vbox.Add(wx.StaticText(self.pnl, label = "Wheel Center Force"))
        self.vbox.Add(self.wheel_centerforce)
        self.vbox.Add(self.wheel_ffb)
        self.vbox.AddSpacer(4)
        self.vbox.Add(wx.StaticText(self.pnl, label = "Wheel Pitch"))
        self.vbox.Add(self.wheel_pitch)
        self.vbox.AddSpacer(4)
        self.vbox.Add(wx.StaticText(self.pnl, label = "Wheel Alpha"))
        self.vbox.Add(self.wheel_alpha)
        self.vbox.Add(self.wheel_transparent_center_box)
        self.vbox.Add(self.wheel_adaptive_center_box)

        self.vbox.AddSpacer(10)
        self.vbox_shifter_degree.Add(wx.StaticText(self.pnl_shifter_degree, label = "Shifter Degree"))
        self.vbox_shifter_degree.Add(self.shifter_degree)
        self.vbox_shifter_alpha.Add(wx.StaticText(self.pnl_shifter_alpha, label = "Shifter Alpha"))
        self.vbox_shifter_alpha.Add(self.shifter_alpha)
        self.vbox_shifter_scale.Add(wx.StaticText(self.pnl_shifter_scale, label = "Shifter Height Scale"))
        self.vbox_shifter_scale.Add(self.shifter_scale)

        self.pnl_shifter_alpha.SetSizerAndFit(self.vbox_shifter_alpha)
        self.pnl_shifter_degree.SetSizerAndFit(self.vbox_shifter_degree)
        self.pnl_shifter_scale.SetSizerAndFit(self.vbox_shifter_scale)

        self.hbox_shifter.Add(self.pnl_shifter_alpha)
        self.hbox_shifter.Add(self.pnl_shifter_degree)
        self.hbox_shifter.Add(self.pnl_shifter_scale)
        self.pnl_shifter.SetSizerAndFit(self.hbox_shifter)
        self.vbox.Add(self.pnl_shifter)
        self.vbox.Add(_decrease_font(
            wx.StaticText(self.pnl, label = "Height 100%=Truck 30%=General")))

        self.vbox.AddSpacer(4)
        self.vbox.Add(self.shifter_adaptive_bounds_box)
        self.vbox.Add(self.shifter_reverse_orientation)

        self.vbox.AddSpacer(10)
        self.vbox.Add(wx.StaticText(self.pnl, label = "Use Joystick as Axis/Button"))
        self.vbox.Add(_decrease_font(
            wx.StaticText(self.pnl, label = "Checked joystick acts as button")))
        self.hbox_joystick.Add(self.j_l_left_button)
        self.hbox_joystick.Add(self.j_l_right_button)
        self.hbox_joystick.Add(self.j_l_up_button)
        self.hbox_joystick.Add(self.j_l_down_button)
        self.hbox_joystick.Add(self.j_r_left_button)
        self.hbox_joystick.Add(self.j_r_right_button)
        self.hbox_joystick.Add(self.j_r_up_button)
        self.hbox_joystick.Add(self.j_r_down_button)
        self.pnl_joystick.SetSizerAndFit(self.hbox_joystick)
        self.vbox.Add(self.pnl_joystick)

        self.vbox.AddSpacer(5)

        self.pnl.SetSizerAndFit(self.vbox)

        self.parent_hbox.AddSpacer(8)
        self.parent_hbox.Add(self.pnl)
        self.parent_hbox.AddSpacer(8)
        self.parent_pnl.SetSizerAndFit(self.parent_hbox)

        self.read_config()
        self.window.Fit()
        self.window.Show(True)

    def read_config(self):
        try:
            self.config = PadConfig()
        except ConfigException as e:
            msg = "Config error: {}. Load defaults?".format(e)
            dlg = wx.MessageDialog(self.pnl, msg, "Config Error", wx.YES_NO | wx.ICON_QUESTION)
            result = dlg.ShowModal() == wx.ID_YES
            dlg.Destroy()
            if result:
                self.config = PadConfig(load_defaults=True)
            else:
                sys.exit(1)
        for key, item in self._config_map.items():
            if type(item) is wx.RadioBox:
                item.SetSelection(item.FindString(getattr(self.config, key)))
            else:
                item.SetValue(getattr(self.config, key))

    def config_change(self, event):
        for key, item in self._config_map.items():
            if type(item) is wx.RadioBox:
                setattr(self.config, key, item.GetString(item.GetSelection()))
            else:
                setattr(self.config, key, item.GetValue())

        p = self.profile_combo.GetValue()
        if p != "":
            self.config.save_to_profile(p)

    def profile_change(self, event):
        v = event.GetEventObject().GetValue()
        self.config.switch_profile(v)
        self.read_config()

    def profile_buttons(self, event):
        l = event.GetEventObject().GetLabel()
        if l == "New":
            p = self.config.save_as_new_profile()
            i = self.profile_combo.Append(p)
            self.profile_combo.SetSelection(i)
        elif l == "Delete":
            i = self.profile_combo.GetSelection()
            if i != wx.NOT_FOUND:
                self.config.delete_profile(self.profile_combo.GetValue())
                self.profile_combo.Delete(i)
        elif l == "Open":
            os.startfile(self.config.get_config_dir())

    def run(self):

        for p in PadConfig.get_profiles():
            self.profile_combo.Append(p)

        p = self.config.find_current_profile()
        if p != "":
            i = self.profile_combo.FindString(p)
            if i == wx.NOT_FOUND:
                raise Exception("Config file not loaded")
            self.profile_combo.SetSelection(i)

        self.app.MainLoop()


def run():
    ConfiguratorApp().run()

if __name__ == '__main__':
    run()