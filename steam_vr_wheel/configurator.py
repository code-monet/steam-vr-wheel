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
        self.profile_open_dir = wx.Button(self.pnl_profile_buttons, label="Open", size=(60,22))
        self.profile_delete = wx.Button(self.pnl_profile_buttons, label="Delete", size=(60,22))

        #
        self.trigger_pre_btn_box = wx.CheckBox(self.pnl, label='Button click when resting finger on triggers (button 31, 32)')
        self.trigger_btn_box = wx.CheckBox(self.pnl, label='Button click when pressing triggers (button 1, 9)')
        self.multibutton_trackpad_box = wx.CheckBox(self.pnl, label='(VIVE) Trackpad clicks has 4 additional zones')
        self.multibutton_trackpad_center_haptic_box = wx.CheckBox(self.pnl,
                                                                  label='(VIVE) Haptic feedback for trackpad button zones')

        ## Hidden
        self.touchpad_always_updates_box = wx.CheckBox(self.pnl, label='Touchpad mapping to axis while untouched (axis move to center when released)')
        self.touchpad_always_updates_box.Hide()
        ##

        self.nb = wx.Notebook(self.pnl)

        self.nb_pnl_wheel_wrapper = wx.Panel(self.nb)
        self.nb_hbox_wheel_wrapper = wx.BoxSizer(wx.HORIZONTAL)
        self.nb_pnl_wheel = wx.Panel(self.nb_pnl_wheel_wrapper)
        self.nb_vbox_wheel = wx.BoxSizer(wx.VERTICAL)

        self.nb_pnl_bike_wrapper = wx.Panel(self.nb)
        self.nb_hbox_bike_wrapper = wx.BoxSizer(wx.HORIZONTAL)
        self.nb_pnl_bike = wx.Panel(self.nb_pnl_bike_wrapper)
        self.nb_vbox_bike = wx.BoxSizer(wx.VERTICAL)

        ## Wheel Page
        self.wheel_grabbed_by_grip_box = wx.CheckBox(self.nb_pnl_wheel, label='Manual wheel grabbing')
        self.wheel_grabbed_by_grip_box_toggle = wx.CheckBox(self.nb_pnl_wheel, label='Grabbing object is NOT toggle')
        self.wheel_show_wheel = wx.CheckBox(self.nb_pnl_wheel, label="Show Wheel Overlay")
        self.wheel_show_wheel.Disable()
        self.wheel_show_hands = wx.CheckBox(self.nb_pnl_wheel, label="Show Hands Overlay")
        self.wheel_show_hands.Disable()
        self.wheel_degrees = wx.SpinCtrl(self.nb_pnl_wheel, name = "Wheel Degrees", max=10000)
        self.wheel_centerforce = wx.SpinCtrl(self.nb_pnl_wheel, name = "Center Force", max=10000)
        self.wheel_ffb = wx.CheckBox(self.nb_pnl_wheel, label="Use Force Feedback instead (tested working on ETS2 only)")
        self.wheel_pitch = wx.SpinCtrl(self.nb_pnl_wheel, name = "Wheel Pitch", min=-30, max=120)
        self.wheel_alpha = wx.SpinCtrl(self.nb_pnl_wheel, name = "Wheel Alpha", max=100)
        self.wheel_transparent_center_box = wx.CheckBox(self.nb_pnl_wheel, label='Wheel becomes transparent while looking at it')

        ### hidden
        self.vertical_wheel_box = wx.CheckBox(self.nb_pnl_wheel, label='Steering wheel is vertical')
        self.vertical_wheel_box.Hide()
        self.joystick_updates_only_when_grabbed_box = wx.CheckBox(self.nb_pnl_wheel, label='Joystick moves only when grabbed (by right grip)')
        self.joystick_updates_only_when_grabbed_box.Hide()
        self.joystick_grabbing_switch_box = wx.CheckBox(self.nb_pnl_wheel, label='Joystick grab is a switch')
        self.joystick_grabbing_switch_box.Hide()
        self.edit_mode_box = wx.CheckBox(self.nb_pnl_wheel, label='Layout edit mode')
        self.edit_mode_box.Hide()
        ###

        ### Shifter
        self.pnl_shifter = wx.Panel(self.nb_pnl_wheel)
        self.hbox_shifter = wx.BoxSizer(wx.HORIZONTAL)

        self.pnl_shifter_degree = wx.Panel(self.pnl_shifter)
        self.vbox_shifter_degree = wx.BoxSizer(wx.VERTICAL)
        self.shifter_degree = wx.SpinCtrl(self.pnl_shifter_degree, name = "Shifter Degree, 80=8 degrees", min=0, max=300)

        self.pnl_shifter_alpha = wx.Panel(self.pnl_shifter)
        self.vbox_shifter_alpha = wx.BoxSizer(wx.VERTICAL)
        self.shifter_alpha = wx.SpinCtrl(self.pnl_shifter_alpha, name = "Shifter Alpha (%), 100%", min=0, max=100)
        
        self.pnl_shifter_scale = wx.Panel(self.pnl_shifter)
        self.vbox_shifter_scale = wx.BoxSizer(wx.VERTICAL)
        self.shifter_scale = wx.SpinCtrl(self.pnl_shifter_scale, name = "Shifter Height Scale (%), 100%", min=10, max=100)
        
        self.shifter_reverse_orientation = wx.RadioBox(self.nb_pnl_wheel, label="Reverse Position",
            choices=["Top Left", "Bottom Left", "Top Right", "Bottom Right"],
            majorDimension=1, style=wx.RA_SPECIFY_ROWS)

        ### Joystick button or axis
        self.pnl_joystick = wx.Panel(self.nb_pnl_wheel)
        self.hbox_joystick = wx.BoxSizer(wx.HORIZONTAL)
        self.j_l_left_button = wx.CheckBox(self.pnl_joystick, label='L ◀')
        self.j_l_right_button = wx.CheckBox(self.pnl_joystick, label='L ▶')
        self.j_l_up_button = wx.CheckBox(self.pnl_joystick, label='L ▲')
        self.j_l_down_button = wx.CheckBox(self.pnl_joystick, label='L ▼')
        self.j_r_left_button = wx.CheckBox(self.pnl_joystick, label='R ◀')
        self.j_r_right_button = wx.CheckBox(self.pnl_joystick, label='R ▶')
        self.j_r_up_button = wx.CheckBox(self.pnl_joystick, label='R ▲')
        self.j_r_down_button = wx.CheckBox(self.pnl_joystick, label='R ▼')

        ## Bike page
        self.bike_mode_absolute_radio = wx.RadioButton(self.nb_pnl_bike, name="Absolute", label="Use Absolute Positioning", style=wx.RB_GROUP)
        self.bike_mode_relative_radio = wx.RadioButton(self.nb_pnl_bike, name="Relative", label="Use Relative Positioning")

        self.bike_show_handlebar = wx.CheckBox(self.nb_pnl_bike, label="Show Handlebar Overlay")
        self.bike_show_hands = wx.CheckBox(self.nb_pnl_bike, label="Show Hands Overlay")
        self.bike_use_ac_server = wx.CheckBox(self.nb_pnl_bike, label="Use Assetto Corsa telemetry to calibrate max lean")

        # -
        self.pnl_bike_angle = wx.Panel(self.nb_pnl_bike)
        self.hbox_bike_angle = wx.BoxSizer(wx.HORIZONTAL)
        
        self.pnl_bike_max_lean = wx.Panel(self.pnl_bike_angle)
        self.vbox_bike_max_lean = wx.BoxSizer(wx.VERTICAL)
        self.bike_max_lean = wx.SpinCtrl(self.pnl_bike_max_lean, name="Lean Angle (Degrees)", min=0, max=90)

        self.pnl_bike_max_steer = wx.Panel(self.pnl_bike_angle)
        self.vbox_bike_max_steer = wx.BoxSizer(wx.VERTICAL)
        self.bike_max_steer = wx.SpinCtrl(self.pnl_bike_max_steer, name="Max Steer (Degrees)", min=0, max=90)

        self.pnl_bike_angle_deadzone = wx.Panel(self.pnl_bike_angle)
        self.vbox_bike_angle_deadzone = wx.BoxSizer(wx.VERTICAL)
        self.bike_angle_deadzone = wx.SpinCtrl(self.pnl_bike_angle_deadzone, name="Deadzone (%)", min=0, max=100)


        # -
        self.bike_throttle_sensitivity = wx.SpinCtrl(self.nb_pnl_bike, name="Throttle Sensitivity (%)", min=1, max=10000)
        self.bike_throttle_decrease_per_sec = wx.SpinCtrl(self.nb_pnl_bike, name="Throttle Decrease per Second (%)", min=0, max=10000)


        ### Absolute box
        self.bike_absolute_box = wx.StaticBox(self.nb_pnl_bike, label="Absolute Mode")
        self.bike_absolute_box_hbox = wx.StaticBoxSizer(self.bike_absolute_box, wx.HORIZONTAL)

        self.bike_absolute_box_inner_pnl = wx.Panel(self.bike_absolute_box)
        self.bike_absolute_box_inner_vbox = wx.BoxSizer(wx.VERTICAL)
        self.bike_handlebar_height = wx.SpinCtrl(self.bike_absolute_box_inner_pnl, name="Handlebar Height (cm)", min=50, max=300)
        self.bike_bound_hand_both = wx.RadioButton(self.bike_absolute_box_inner_pnl, name="Both Hands", label="Both Hands", style=wx.RB_GROUP)
        self.bike_bound_hand_left = wx.RadioButton(self.bike_absolute_box_inner_pnl, name="Left", label="Left")
        self.bike_bound_hand_right = wx.RadioButton(self.bike_absolute_box_inner_pnl, name="Right", label="Right")


        ### Relative box
        self.bike_relative_box = wx.StaticBox(self.nb_pnl_bike, label="Relative Mode")
        self.bike_relative_box_hbox = wx.StaticBoxSizer(self.bike_relative_box, wx.HORIZONTAL)

        self.bike_relative_box_inner_pnl = wx.Panel(self.bike_relative_box)
        self.bike_relative_box_inner_vbox = wx.BoxSizer(wx.VERTICAL)

        self.bike_relative_sensitivity = wx.SpinCtrl(self.bike_relative_box_inner_pnl, name="Relative Sensitivity (%)", min=1, max=10000)


        # BINDINGS

        # Profile binds
        self.profile_combo.Bind(wx.EVT_COMBOBOX, self.profile_change)
        self.profile_new.Bind(wx.EVT_BUTTON, self.profile_buttons)
        self.profile_delete.Bind(wx.EVT_BUTTON, self.profile_buttons)
        self.profile_open_dir.Bind(wx.EVT_BUTTON, self.profile_buttons)

        # Wheel
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

        ## Shifter
        self.shifter_degree.Bind(wx.EVT_SPINCTRL, self.config_change)
        self.shifter_alpha.Bind(wx.EVT_SPINCTRL, self.config_change)
        self.shifter_scale.Bind(wx.EVT_SPINCTRL, self.config_change)
        self.shifter_reverse_orientation.Bind(wx.EVT_RADIOBOX, self.config_change)

        ## Joystick button or axis
        self.j_l_left_button.Bind(wx.EVT_CHECKBOX, self.config_change)
        self.j_l_right_button.Bind(wx.EVT_CHECKBOX, self.config_change)
        self.j_l_up_button.Bind(wx.EVT_CHECKBOX, self.config_change)
        self.j_l_down_button.Bind(wx.EVT_CHECKBOX, self.config_change)
        self.j_r_left_button.Bind(wx.EVT_CHECKBOX, self.config_change)
        self.j_r_right_button.Bind(wx.EVT_CHECKBOX, self.config_change)
        self.j_r_up_button.Bind(wx.EVT_CHECKBOX, self.config_change)
        self.j_r_down_button.Bind(wx.EVT_CHECKBOX, self.config_change)

        # Bike

        self.bike_show_handlebar.Bind(wx.EVT_CHECKBOX, self.config_change)
        self.bike_show_hands.Bind(wx.EVT_CHECKBOX, self.config_change)
        self.bike_use_ac_server.Bind(wx.EVT_CHECKBOX, self.config_change)

        self.bike_throttle_sensitivity.Bind(wx.EVT_SPINCTRL, self.config_change)
        self.bike_throttle_decrease_per_sec.Bind(wx.EVT_SPINCTRL, self.config_change)
        self.bike_max_lean.Bind(wx.EVT_SPINCTRL, self.config_change)
        self.bike_max_steer.Bind(wx.EVT_SPINCTRL, self.config_change)
        self.bike_angle_deadzone.Bind(wx.EVT_SPINCTRL, self.config_change)
        self.bike_handlebar_height.Bind(wx.EVT_SPINCTRL, self.config_change)
        self.bike_relative_sensitivity.Bind(wx.EVT_SPINCTRL, self.config_change)

        self.bike_mode_absolute_radio.Bind(wx.EVT_RADIOBUTTON, self.config_change)
        self.bike_mode_relative_radio.Bind(wx.EVT_RADIOBUTTON, self.config_change)
        self.bike_bound_hand_both.Bind(wx.EVT_RADIOBUTTON, self.config_change)
        self.bike_bound_hand_left.Bind(wx.EVT_RADIOBUTTON, self.config_change)
        self.bike_bound_hand_right.Bind(wx.EVT_RADIOBUTTON, self.config_change)

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

                                shifter_degree=self.shifter_degree,
                                shifter_alpha=self.shifter_alpha,
                                shifter_scale=self.shifter_scale,
                                shifter_reverse_orientation=self.shifter_reverse_orientation,

                                j_l_left_button=self.j_l_left_button,
                                j_l_right_button=self.j_l_right_button,
                                j_l_up_button=self.j_l_up_button,
                                j_l_down_button=self.j_l_down_button,
                                j_r_left_button=self.j_r_left_button,
                                j_r_right_button=self.j_r_right_button,
                                j_r_up_button=self.j_r_up_button,
                                j_r_down_button=self.j_r_down_button,

                                bike_show_handlebar=self.bike_show_handlebar,
                                bike_show_hands=self.bike_show_hands,
                                bike_use_ac_server=self.bike_use_ac_server,
                                bike_handlebar_height=self.bike_handlebar_height,
                                bike_max_lean=self.bike_max_lean,
                                bike_max_steer=self.bike_max_steer,
                                bike_angle_deadzone=self.bike_angle_deadzone,
                                bike_throttle_sensitivity=self.bike_throttle_sensitivity,
                                bike_throttle_decrease_per_sec=self.bike_throttle_decrease_per_sec,
                                bike_relative_sensitivity=self.bike_relative_sensitivity,

                                bike_mode=[self.bike_mode_absolute_radio, self.bike_mode_relative_radio],
                                bike_bound_hand=[self.bike_bound_hand_both, self.bike_bound_hand_left, self.bike_bound_hand_right]

                                )

        # Adding items
        self.vbox.AddSpacer(5)

        self.vbox.Add(wx.StaticText(self.pnl, label = "Selected Profile"))
        self.hbox_profile_buttons.Add(self.profile_combo)
        self.hbox_profile_buttons.AddSpacer(6)
        self.hbox_profile_buttons.Add(self.profile_new)
        self.hbox_profile_buttons.Add(self.profile_open_dir)
        self.hbox_profile_buttons.Add(self.profile_delete)
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

        ## Adding items to Wheel page
        self.nb_vbox_wheel.AddSpacer(5)
        self.nb_vbox_wheel.Add(self.vertical_wheel_box)
        self.nb_vbox_wheel.Add(self.joystick_updates_only_when_grabbed_box)
        self.nb_vbox_wheel.Add(self.joystick_grabbing_switch_box)
        self.nb_vbox_wheel.Add(self.edit_mode_box)
        self.nb_vbox_wheel.Add(self.wheel_grabbed_by_grip_box)
        self.nb_vbox_wheel.Add(self.wheel_grabbed_by_grip_box_toggle)
        self.nb_vbox_wheel.Add(self.wheel_show_wheel)
        self.nb_vbox_wheel.Add(self.wheel_show_hands)
        self.nb_vbox_wheel.AddSpacer(10)
        self.nb_vbox_wheel.Add(wx.StaticText(self.nb_pnl_wheel, label = "Wheel Degrees"))
        self.nb_vbox_wheel.Add(_decrease_font(
            wx.StaticText(self.nb_pnl_wheel, label = "360=F1 540 - 1080=Rally car 1440=Default 900 - 1800=Truck")))
        self.nb_vbox_wheel.Add(self.wheel_degrees)
        self.nb_vbox_wheel.AddSpacer(4)
        self.nb_vbox_wheel.Add(wx.StaticText(self.nb_pnl_wheel, label = "Wheel Center Force"))
        self.nb_vbox_wheel.Add(self.wheel_centerforce)
        self.nb_vbox_wheel.Add(self.wheel_ffb)
        self.nb_vbox_wheel.AddSpacer(4)
        self.nb_vbox_wheel.Add(wx.StaticText(self.nb_pnl_wheel, label = "Wheel Pitch"))
        self.nb_vbox_wheel.Add(self.wheel_pitch)
        self.nb_vbox_wheel.AddSpacer(4)
        self.nb_vbox_wheel.Add(wx.StaticText(self.nb_pnl_wheel, label = "Wheel Alpha"))
        self.nb_vbox_wheel.Add(self.wheel_alpha)
        self.nb_vbox_wheel.Add(self.wheel_transparent_center_box)

        self.nb_vbox_wheel.AddSpacer(10)
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
        self.nb_vbox_wheel.Add(self.pnl_shifter)
        self.nb_vbox_wheel.Add(_decrease_font(
            wx.StaticText(self.nb_pnl_wheel, label = "Height 100%=Truck 30%=General")))
        self.nb_vbox_wheel.Add(_decrease_font(
            wx.StaticText(self.nb_pnl_wheel, label = "Degree 80=8 degrees 151=15.1 degrees")))

        self.nb_vbox_wheel.AddSpacer(4)
        self.nb_vbox_wheel.Add(self.shifter_reverse_orientation)

        self.nb_vbox_wheel.AddSpacer(10)
        self.nb_vbox_wheel.Add(wx.StaticText(self.nb_pnl_wheel, label = "Use Joystick as Axis/Button"))
        self.nb_vbox_wheel.Add(_decrease_font(
            wx.StaticText(self.nb_pnl_wheel, label = "Checked joystick acts as button")))
        self.nb_vbox_wheel.AddSpacer(6)
        self.hbox_joystick.Add(self.j_l_left_button)
        self.hbox_joystick.Add(self.j_l_right_button)
        self.hbox_joystick.Add(self.j_l_up_button)
        self.hbox_joystick.Add(self.j_l_down_button)
        self.hbox_joystick.Add(self.j_r_left_button)
        self.hbox_joystick.Add(self.j_r_right_button)
        self.hbox_joystick.Add(self.j_r_up_button)
        self.hbox_joystick.Add(self.j_r_down_button)
        self.pnl_joystick.SetSizerAndFit(self.hbox_joystick)
        self.nb_vbox_wheel.Add(self.pnl_joystick)

        self.nb_vbox_wheel.AddSpacer(5)

        self.nb_pnl_wheel.SetSizerAndFit(self.nb_vbox_wheel)

        self.nb_hbox_wheel_wrapper.AddSpacer(6)
        self.nb_hbox_wheel_wrapper.Add(self.nb_pnl_wheel)
        self.nb_hbox_wheel_wrapper.AddSpacer(6)
        self.nb_pnl_wheel_wrapper.SetSizerAndFit(self.nb_hbox_wheel_wrapper)
        self.nb.AddPage(self.nb_pnl_wheel_wrapper, "Wheel")


        ## Adding items to Bike page
        self.nb_vbox_bike.AddSpacer(5)

        self.nb_vbox_bike.Add(self.bike_show_handlebar)
        self.nb_vbox_bike.Add(self.bike_show_hands)
        self.nb_vbox_bike.Add(self.bike_use_ac_server)

        self.nb_vbox_bike.AddSpacer(4)

        self.vbox_bike_max_lean.Add(wx.StaticText(self.pnl_bike_max_lean, label="Max Lean Angle"))
        self.vbox_bike_max_lean.Add(self.bike_max_lean)
        self.vbox_bike_max_steer.Add(wx.StaticText(self.pnl_bike_max_steer, label="Max Steer Angle"))
        self.vbox_bike_max_steer.Add(self.bike_max_steer)
        self.vbox_bike_angle_deadzone.Add(wx.StaticText(self.pnl_bike_angle_deadzone, label="Deadzone (%)"))
        self.vbox_bike_angle_deadzone.Add(self.bike_angle_deadzone)

        self.pnl_bike_max_lean.SetSizerAndFit(self.vbox_bike_max_lean)
        self.pnl_bike_max_steer.SetSizerAndFit(self.vbox_bike_max_steer)
        self.pnl_bike_angle_deadzone.SetSizerAndFit(self.vbox_bike_angle_deadzone)

        self.hbox_bike_angle.Add(self.pnl_bike_max_lean)
        self.hbox_bike_angle.Add(self.pnl_bike_max_steer)
        self.hbox_bike_angle.Add(self.pnl_bike_angle_deadzone)
        self.pnl_bike_angle.SetSizerAndFit(self.hbox_bike_angle)
        self.nb_vbox_bike.Add(self.pnl_bike_angle)

        self.nb_vbox_bike.AddSpacer(4)
        self.nb_vbox_bike.Add(wx.StaticText(self.nb_pnl_bike, label="Throttle Sensitivity (%)"))
        self.nb_vbox_bike.Add(self.bike_throttle_sensitivity)
        self.nb_vbox_bike.AddSpacer(4)
        self.nb_vbox_bike.Add(wx.StaticText(self.nb_pnl_bike, label="Throttle Decrease per Second (%)"))
        self.nb_vbox_bike.Add(self.bike_throttle_decrease_per_sec)
        self.nb_vbox_bike.AddSpacer(10)


        ### Absolute positioning mode
        self.nb_vbox_bike.Add(self.bike_mode_absolute_radio)
        self.nb_vbox_bike.Add(_decrease_font(
            wx.StaticText(self.nb_pnl_bike, label="Position of hands determines the lean angle")))
        self.nb_vbox_bike.AddSpacer(4)

        self.bike_absolute_box_hbox.AddSpacer(5)

        self.bike_absolute_box_inner_vbox.Add(wx.StaticText(self.bike_absolute_box_inner_pnl, label="In-game Handlebar Height (cm)"))
        self.bike_absolute_box_inner_vbox.Add(_decrease_font(
            wx.StaticText(self.bike_absolute_box_inner_pnl, label="In-game bike model handlebar's height from the floor")))
        self.bike_absolute_box_inner_vbox.Add(self.bike_handlebar_height)
        self.bike_absolute_box_inner_vbox.AddSpacer(8)

        self.bike_absolute_box_inner_vbox.Add(wx.StaticText(self.bike_absolute_box_inner_pnl, label="Bound Hands"))
        self.bike_absolute_box_inner_vbox.Add(_decrease_font(
            wx.StaticText(self.bike_absolute_box_inner_pnl, label="Selected hands are bound to the handlebar\nUnbound hand is free to move")))
        self.bike_absolute_box_inner_vbox.AddSpacer(3)
        self.bike_absolute_box_inner_vbox.Add(self.bike_bound_hand_both)
        self.bike_absolute_box_inner_vbox.Add(self.bike_bound_hand_left)
        self.bike_absolute_box_inner_vbox.Add(self.bike_bound_hand_right)
        self.bike_absolute_box_inner_vbox.AddSpacer(5)

        self.bike_absolute_box_inner_pnl.SetSizerAndFit(self.bike_absolute_box_inner_vbox)
        self.bike_absolute_box_hbox.Add(self.bike_absolute_box_inner_pnl)

        self.bike_absolute_box_hbox.AddSpacer(50)
        self.bike_absolute_box.Fit()
        self.nb_vbox_bike.Add(self.bike_absolute_box_hbox) # NOTE When adding staticBox add its sizer not the box

        ### Relative positioning mode
        self.nb_vbox_bike.AddSpacer(10)
        self.nb_vbox_bike.Add(self.bike_mode_relative_radio)
        self.nb_vbox_bike.Add(_decrease_font(
            wx.StaticText(self.nb_pnl_bike, label="Angle between two hands determine the lean angle")))
        self.nb_vbox_bike.AddSpacer(4)

        self.bike_relative_box_hbox.AddSpacer(5)

        self.bike_relative_box_inner_vbox.Add(wx.StaticText(self.bike_relative_box_inner_pnl, label="Relative Sensitivity (%)"))
        self.bike_relative_box_inner_vbox.Add(self.bike_relative_sensitivity)
        self.bike_relative_box_inner_vbox.AddSpacer(5)

        self.bike_relative_box_inner_pnl.SetSizerAndFit(self.bike_relative_box_inner_vbox)
        self.bike_relative_box_hbox.Add(self.bike_relative_box_inner_pnl)

        self.bike_relative_box_hbox.AddSpacer(50)
        self.bike_relative_box.Fit()
        self.nb_vbox_bike.Add(self.bike_relative_box_hbox) # NOTE When adding staticBox add its sizer not the box


        ##
        self.nb_vbox_bike.AddSpacer(5)
        self.nb_pnl_bike.SetSizerAndFit(self.nb_vbox_bike)

        self.nb_hbox_bike_wrapper.AddSpacer(6)
        self.nb_hbox_bike_wrapper.Add(self.nb_pnl_bike) # NOTE: if you add boxsizer, not panel, it will take long for the window to close
        self.nb_hbox_bike_wrapper.AddSpacer(6)
        self.nb_pnl_bike_wrapper.SetSizerAndFit(self.nb_hbox_bike_wrapper)
        self.nb.AddPage(self.nb_pnl_bike_wrapper, "Bike")

        self.vbox.AddSpacer(5)
        self.vbox.Add(self.nb)
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

        #
        self.profile_combo.Clear()
        for p in PadConfig.get_profiles():
            self.profile_combo.Append(p)

        p = self.config.find_current_profile()
        if p != "":
            i = self.profile_combo.FindString(p)
            if i == wx.NOT_FOUND:
                raise Exception("Config file not loaded")
            self.profile_combo.SetSelection(i)
        else:
            self.profile_combo.SetSelection(wx.NOT_FOUND)

        #
        for key, item in self._config_map.items():
            if isinstance(item, list):
                value = getattr(self.config, key)
                for each in item:
                    if each.GetName() == value:
                        each.SetValue(True)
                    else:
                        each.SetValue(False)
            elif type(item) is wx.RadioBox:
                item.SetSelection(item.FindString(getattr(self.config, key)))
            else:
                item.SetValue(getattr(self.config, key))

    def config_change(self, event):
        for key, item in self._config_map.items():
            if isinstance(item, list):
                value = ""
                for each in item:
                    if each.GetValue():
                        value = each.GetName()
                setattr(self.config, key, value)
            elif type(item) is wx.RadioBox:
                setattr(self.config, key, item.GetString(item.GetSelection()))
            else:
                setattr(self.config, key, item.GetValue())

        p = self.profile_combo.GetValue()
        if p != "":
            self.config.save_to_profile(p)

    def profile_change(self, event):
        cb = event.GetEventObject()
        self.config.switch_profile(cb.GetValue())
        self.read_config()

    def profile_buttons(self, event):
        l = event.GetEventObject().GetLabel()
        if l == "New":

            fd = wx.FileDialog(self.pnl, "New Profile",
                self.config.get_config_dir(), "new-profile.json",
                "*.json|*.json",
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            if fd.ShowModal() == wx.ID_CANCEL:
                return

            p = os.path.basename(fd.GetPath())
            self.config.config_name = p
            self.config.save_as_new_profile(p)
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
        self.app.MainLoop()



def run():
    ConfiguratorApp().run()

if __name__ == '__main__':
    run()