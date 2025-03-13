import sys
import wx
import os

from steam_vr_wheel import PadConfig, ConfigException, DEFAULT_CONFIG
from steam_vr_wheel.util import expand_to_array, is_array


class HelperPanel(wx.Panel):
    def __init__(self, parent, pad=0, vertical=True, label=None, **kwargs):

        super().__init__(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        if label is not None:
            wrap_v = wx.StaticBox(self, label=label)
            wrap_vbox = wx.StaticBoxSizer(wrap_v, wx.VERTICAL)
        else:
            wrap_v = wx.Panel(self)
            wrap_vbox = wx.BoxSizer(wx.VERTICAL)
            wrap_v.SetSizer(wrap_vbox)

        wrap_h = wx.Panel(wrap_v)
        wrap_hbox = wx.BoxSizer(wx.HORIZONTAL)
        wrap_h.SetSizer(wrap_hbox)

        # Check size
        pad = expand_to_array(pad)
        pad = pad * int(4 / len(pad))
        self._size = (-1, -1)
        if 'size' in kwargs:
            size = list(kwargs['size'])
            if size[0] > 0:
                size[0] -= pad[1] + pad[3]
            if size[1] > 0:
                size[1] -= pad[0] + pad[2]
            kwargs['size'] = size
            self._size = size

        inner = wx.Panel(wrap_h, **kwargs)
        inner_sizer = wx.BoxSizer(wx.VERTICAL if vertical else wx.HORIZONTAL)
        inner.SetSizer(inner_sizer)

        wrap_hbox.AddSpacer(pad[3])
        wrap_hbox.Add(inner, proportion=1, flag=wx.EXPAND | wx.ALL)
        wrap_hbox.AddSpacer(pad[1])

        wrap_vbox.AddSpacer(pad[0])
        wrap_vbox.Add(wrap_h, proportion=1, flag=wx.EXPAND | wx.ALL)
        wrap_vbox.AddSpacer(pad[2])

        if isinstance(wrap_v, wx.StaticBox):
            # NOTE When adding staticBox add its sizer not the box
            # otherwise there is some delay when creating or destroying main window
            sizer.Add(wrap_vbox, proportion=1, flag=wx.EXPAND | wx.ALL)
        else:
            # NOTE: if you add boxsizer, not panel, it will take long for the window to close
            sizer.Add(wrap_v, proportion=1, flag=wx.EXPAND | wx.ALL)

        self._wrap_v = wrap_v
        self._wrap_vbox = wrap_vbox
        self._wrap_h = wrap_h
        self._inner = inner
        self._inner_sizer = inner_sizer

    def Add(self, win, *args, **kw):
        self._inner_sizer.Add(win, *args, **kw)

    def AddSpacer(self, i):
        self._inner_sizer.AddSpacer(i)

    def Fit(self):
        self._inner.Fit()
        self._wrap_h.Fit()
        self._wrap_v.Fit()
        super().Fit()
    
    def AddChild(self, child):
        if hasattr(self, '_inner'):
            # Intercept calls like wx.Panel(helperPanel)
            # so that it is added to inner rather than to self
            self._inner.AddChild(child)
        else:
            super().AddChild(child)

    def SetSizerAndFit(self):
        raise RuntimeError("Not allowed")

class HelperText(wx.StaticText):
    def __init__(self, parent, is_muted=False, label="Label", *args, **kwargs):

        label = "\n".join(a.strip() for a in label.split("\n"))

        super().__init__(parent, label=label, *args, **kwargs)

        if is_muted:
            #f = self.GetFont()
            #p = f.GetPointSize()
            #f.SetPointSize(p-1)
            #self.SetFont(f)
            self.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))

class LabeledSpinCtrl(wx.Panel):
    def __init__(self, parent, is_double=False, *args, **kwargs):
        """
        Composite control that contains a StaticText and a SpinCtrl.
        It exposes the SpinCtrl API via delegation.
        
        :param parent: Parent window.
        :param name: Label to display.
        :param min_val: Minimum SpinCtrl value.
        :param max_val: Maximum SpinCtrl value.
        :param initial: Initial value.
        :param kwargs: Additional keyword arguments for wx.SpinCtrl.
        """
        super().__init__(parent)
        
        # Create a horizontal sizer to arrange label and spin control.
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Create the label.
        pnl_label = wx.Panel(self)
        pnl_label_sizer = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(pnl_label, label=kwargs['name'])

        # Create the spin control.
        self.is_double = is_double
        if is_double:
            self.spin = wx.SpinCtrlDouble(self, *args, **kwargs)
            self.spin.SetDigits(1)
        else:
            self.spin = wx.SpinCtrl(self, *args, **kwargs)

        # Center align
        label_height = label.GetBestSize()[1]
        spin_height = self.spin.GetBestSize()[1]
        pnl_label_sizer.AddSpacer(1 + int((spin_height - label_height) / 2))
        pnl_label_sizer.Add(label)
        pnl_label.SetSizerAndFit(pnl_label_sizer)
        
        # Add the label, with proportion=1 so it expands horizontally.
        sizer.Add(pnl_label, proportion=1, flag=wx.EXPAND | wx.ALL)
        # Add the spin control with fixed size.
        sizer.Add(self.spin, proportion=0, flag=wx.ALL)
        
        self.SetSizerAndFit(sizer)

    def __getattr__(self, attr):
        """
        Delegate attribute access to the spin control.
        This means that if a method or property is not found on the LabeledSpinCtrl,
        Python will try to access it on self.spin.
        """
        return getattr(self.spin, attr)


PAD_sm = 4
PAD_m = 12
PAD_lg = 18
PAD_xl = 30

class ConfiguratorApp:

    def __init__(self):

        self._config_map = dict()

        deferred = []
        def defer_fit(win):
            deferred.append(win)

        self.app = wx.App()
        self.window = wx.Frame(None, title="steam-vr-wheel Configuration", \
            style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.MINIMIZE_BOX ^ wx.MAXIMIZE_BOX)
        defer_fit(self.window)

        self.pnl = HelperPanel(self.window, (10, 12, 24, 12), size=(500, -1))
        defer_fit(self.pnl)

        #
        self.pnl_general = HelperPanel(self.pnl, PAD_m)
        self.pnl.Add(self.pnl_general, flag=wx.EXPAND)

        self.pnl_general.Add(wx.StaticText(self.pnl_general, label = "Selected Profile"))

        self.pnl_profile_buttons = HelperPanel(self.pnl_general, vertical=False)
        self.pnl_general.Add(self.pnl_profile_buttons, flag=wx.EXPAND)

        self.profile_combo = wx.ComboBox(self.pnl_profile_buttons, style=wx.CB_READONLY, size=(160,24))
        self.pnl_profile_buttons.Add(self.profile_combo)
        self.pnl_profile_buttons.AddSpacer(6)

        self.profile_new = wx.Button(self.pnl_profile_buttons, label="Save", size=(60,22))
        self.profile_open_dir = wx.Button(self.pnl_profile_buttons, label="Open", size=(60,22))
        self.profile_delete = wx.Button(self.pnl_profile_buttons, label="Delete", size=(60,22))
        self.pnl_profile_buttons.Add(self.profile_new)
        self.pnl_profile_buttons.Add(self.profile_open_dir)
        self.pnl_profile_buttons.Add(self.profile_delete)

        self.pnl_general.AddSpacer(PAD_lg)

        self.trigger_pre_btn_box = wx.CheckBox(self.pnl_general, label='Button click when you rest finger on triggers')
        self.trigger_btn_box = wx.CheckBox(self.pnl_general, label='Button click when you press triggers')
        self.pnl_general.Add(self.trigger_pre_btn_box)
        self.pnl_general.Add(self.trigger_btn_box)

        self.pnl_general.AddSpacer(PAD_m)

        self.sfx_volume = LabeledSpinCtrl(self.pnl_general, name="SFX Volume (%)", min=0, max=100, size=(120,-1))
        self.pnl_general.Add(self.sfx_volume, flag=wx.EXPAND)
        self.pnl_general.AddSpacer(PAD_sm)
        self.haptic_intensity = LabeledSpinCtrl(self.pnl_general, name="Haptic Intensity (%)", min=0, max=200, size=(120,-1))
        self.pnl_general.Add(self.haptic_intensity, flag=wx.EXPAND)

        ## Joystick button or axis

        PAGE_PAD = (16, 12, 30, 12)
        FRAME_PAD = (12, 8, 16, 8)
        self.nb = wx.Notebook(self.pnl, style=wx.NB_MULTILINE)
        self.pnl.Add(self.nb, flag=wx.EXPAND)

        ## Joystick page
        self.nb_pnl_joystick = HelperPanel(self.nb, PAGE_PAD)
        self.nb.AddPage(self.nb_pnl_joystick, " Joystick ")

        self.axis_deadzone = LabeledSpinCtrl(self.nb_pnl_joystick, name="Axis Deadzone (%)", min=0, max=100, size=(120, -1))
        self.nb_pnl_joystick.Add(self.axis_deadzone, flag=wx.EXPAND)
        self.nb_pnl_joystick.AddSpacer(PAD_xl)
        
        self.pnl_joystick_frame = HelperPanel(self.nb_pnl_joystick, FRAME_PAD, label="Axis or Button")
        self.nb_pnl_joystick.Add(self.pnl_joystick_frame, flag=wx.EXPAND)

        self.pnl_joystick_frame.Add(HelperText(self.pnl_joystick_frame, is_muted=True, label="Checked joystick direction will act as button"))
        self.pnl_joystick_frame.AddSpacer(PAD_m)

        self.pnl_joystick = HelperPanel(self.pnl_joystick_frame, vertical=False)
        self.pnl_joystick_frame.Add(self.pnl_joystick, flag=wx.EXPAND)

        self.j_l_left_button = wx.CheckBox(self.pnl_joystick, label='L ◀')
        self.j_l_right_button = wx.CheckBox(self.pnl_joystick, label='L ▶')
        self.j_l_up_button = wx.CheckBox(self.pnl_joystick, label='L ▲')
        self.j_l_down_button = wx.CheckBox(self.pnl_joystick, label='L ▼')
        self.j_r_left_button = wx.CheckBox(self.pnl_joystick, label='R ◀')
        self.j_r_right_button = wx.CheckBox(self.pnl_joystick, label='R ▶')
        self.j_r_up_button = wx.CheckBox(self.pnl_joystick, label='R ▲')
        self.j_r_down_button = wx.CheckBox(self.pnl_joystick, label='R ▼')
        self.pnl_joystick.Add(self.j_l_left_button); self.pnl_joystick.AddSpacer(6)
        self.pnl_joystick.Add(self.j_l_right_button); self.pnl_joystick.AddSpacer(6)
        self.pnl_joystick.Add(self.j_l_up_button); self.pnl_joystick.AddSpacer(6)
        self.pnl_joystick.Add(self.j_l_down_button); self.pnl_joystick.AddSpacer(6)
        self.pnl_joystick.Add(self.j_r_left_button); self.pnl_joystick.AddSpacer(6)
        self.pnl_joystick.Add(self.j_r_right_button); self.pnl_joystick.AddSpacer(6)
        self.pnl_joystick.Add(self.j_r_up_button); self.pnl_joystick.AddSpacer(6)
        self.pnl_joystick.Add(self.j_r_down_button)

        self.nb_pnl_joystick.AddSpacer(PAD_xl)
        self.multibutton_trackpad_box = wx.CheckBox(self.nb_pnl_joystick, label='Joystick has 4 additional click regions')
        self.nb_pnl_joystick.Add(self.multibutton_trackpad_box)
        self.nb_pnl_joystick.AddSpacer(PAD_sm)
        self.nb_pnl_joystick.Add(HelperText(self.nb_pnl_joystick, 
            is_muted=True,
            label='''Joysticks (or trackpads on VIVE) have 4 more buttons registered
                     Center, left, right, down, and up totaling 5 click regions'''))

        ## Wheel Page
        self.nb_pnl_wheel = HelperPanel(self.nb, PAGE_PAD)
        self.nb.AddPage(self.nb_pnl_wheel, " Wheel ")

        self.wheel_degrees = LabeledSpinCtrl(self.nb_pnl_wheel, name = "Wheel Rotation (Degrees)", max=10000, size=(120,-1))
        self.nb_pnl_wheel.Add(self.wheel_degrees, flag=wx.EXPAND)
        self.nb_pnl_wheel.AddSpacer(PAD_sm)
        self.nb_pnl_wheel.Add(
            HelperText(self.nb_pnl_wheel, is_muted=True, label="360=F1 540 - 1080=Rally car 1440=Default 900 - 1800=Truck"))
        self.nb_pnl_wheel.AddSpacer(PAD_xl)

        self.wheel_pitch = LabeledSpinCtrl(self.nb_pnl_wheel, name = "Wheel Tilt (Degrees)", min=-30, max=120, size=(120,-1))
        self.nb_pnl_wheel.Add(self.wheel_pitch, flag=wx.EXPAND)
        self.nb_pnl_wheel.AddSpacer(PAD_sm)

        self.wheel_alpha = LabeledSpinCtrl(self.nb_pnl_wheel, name = "Wheel Alpha (%)", max=100, size=(120,-1))
        self.wheel_transparent_center_box = wx.CheckBox(self.nb_pnl_wheel, label='Wheel becomes transparent while looking at it')
        self.nb_pnl_wheel.Add(self.wheel_alpha, flag=wx.EXPAND)
        self.nb_pnl_wheel.AddSpacer(PAD_sm)
        self.nb_pnl_wheel.Add(self.wheel_transparent_center_box)
        self.nb_pnl_wheel.AddSpacer(PAD_xl)

        self.wheel_centering = HelperPanel(self.nb_pnl_wheel, FRAME_PAD, label="Wheel Centering")
        self.nb_pnl_wheel.Add(self.wheel_centering, flag=wx.EXPAND)

        self.wheel_centerforce = LabeledSpinCtrl(self.wheel_centering, name = "Center Force (%)", max=10000, size=(120,-1))
        self.wheel_ffb = wx.CheckBox(self.wheel_centering, label="Use Force Feedback to center the wheel")
        self.wheel_ffb_haptic = wx.CheckBox(self.wheel_centering, label="Force Feedback haptic on bumpy roads")
        self.wheel_centering.Add(self.wheel_centerforce, flag=wx.EXPAND)
        self.wheel_centering.AddSpacer(PAD_lg)
        self.wheel_centering.Add(self.wheel_ffb)
        self.wheel_centering.Add(self.wheel_ffb_haptic)
        self.nb_pnl_wheel.AddSpacer(PAD_xl)

        self.wheel_grab_behavior = HelperPanel(self.nb_pnl_wheel, FRAME_PAD, label="Grab Behavior")
        self.nb_pnl_wheel.Add(self.wheel_grab_behavior, flag=wx.EXPAND)

        self.wheel_grabbed_by_grip_box = wx.CheckBox(self.wheel_grab_behavior, label='Manual wheel grabbing')
        self.wheel_grabbed_by_grip_box_toggle = wx.CheckBox(self.wheel_grab_behavior, label='Grabbing object is NOT toggle')
        self.wheel_grab_behavior.Add(self.wheel_grabbed_by_grip_box)
        self.wheel_grab_behavior.Add(self.wheel_grabbed_by_grip_box_toggle)

        ## Shifter page
        self.nb_pnl_shifter = HelperPanel(self.nb, PAGE_PAD)
        self.nb.AddPage(self.nb_pnl_shifter, " H Shifter ")

        self.shifter_degree = LabeledSpinCtrl(self.nb_pnl_shifter, is_double=True, name="Shifter Tilt (Degrees)", inc=0.1, min=0.0, max=30.0, size=(120,-1))
        self.nb_pnl_shifter.Add(self.shifter_degree, flag=wx.EXPAND)
        self.nb_pnl_shifter.AddSpacer(PAD_sm)

        self.shifter_alpha = LabeledSpinCtrl(self.nb_pnl_shifter, name = "Shifter Alpha (%)", min=0, max=100, size=(120,-1))
        self.nb_pnl_shifter.Add(self.shifter_alpha, flag=wx.EXPAND)
        self.nb_pnl_shifter.AddSpacer(PAD_sm)

        self.shifter_scale = LabeledSpinCtrl(self.nb_pnl_shifter, name = "Shifter Height Scale (%)", min=10, max=100, size=(120,-1))
        self.nb_pnl_shifter.Add(self.shifter_scale, flag=wx.EXPAND)
        self.nb_pnl_shifter.Add(
            HelperText(self.nb_pnl_shifter, is_muted=True, label="Height Scale 100%=Truck Height Scale 30%=General"))
        self.nb_pnl_shifter.AddSpacer(PAD_xl)
        
        self.shifter_sequential = wx.CheckBox(self.nb_pnl_shifter, label="Sequential mode")
        self.nb_pnl_shifter.Add(self.shifter_sequential)
        self.nb_pnl_shifter.AddSpacer(PAD_xl)

        shifter_rev = HelperPanel(self.nb_pnl_shifter, FRAME_PAD, vertical=False, label="Reverse Position")
        self.nb_pnl_shifter.Add(shifter_rev, flag=wx.EXPAND)

        shifter_rev_tl = wx.RadioButton(shifter_rev, name="Top Left", label="Top Left", style=wx.RB_GROUP)
        shifter_rev_tr = wx.RadioButton(shifter_rev, name="Top Right", label="Top Right")
        shifter_rev_bl = wx.RadioButton(shifter_rev, name="Bottom Left", label="Bottom Left")
        shifter_rev_br = wx.RadioButton(shifter_rev, name="Bottom Right", label="Bottom Right")
        shifter_rev.Add(shifter_rev_tl); shifter_rev.AddSpacer(6)
        shifter_rev.Add(shifter_rev_tr); shifter_rev.AddSpacer(6)
        shifter_rev.Add(shifter_rev_bl); shifter_rev.AddSpacer(6)
        shifter_rev.Add(shifter_rev_br)

        ## Bike page
        self.nb_pnl_bike = HelperPanel(self.nb, PAGE_PAD)
        self.nb.AddPage(self.nb_pnl_bike, " Bike ")

        self.bike_show_handlebar = wx.CheckBox(self.nb_pnl_bike, label="Show Handlebar Overlay")
        self.bike_show_hands = wx.CheckBox(self.nb_pnl_bike, label="Show Hands Overlay")
        self.bike_use_ac_server = wx.CheckBox(self.nb_pnl_bike, label="Use Assetto Corsa telemetry to calibrate max lean")
        self.nb_pnl_bike.Add(self.bike_show_handlebar)
        self.nb_pnl_bike.Add(self.bike_show_hands)
        self.nb_pnl_bike.Add(self.bike_use_ac_server)
        self.nb_pnl_bike.AddSpacer(PAD_sm)

        self.bike_max_lean = LabeledSpinCtrl(self.nb_pnl_bike, name="Lean Angle (Degrees)", min=0, max=90, size=(120,-1))
        self.bike_max_steer = LabeledSpinCtrl(self.nb_pnl_bike, name="Max Steer (Degrees)", min=0, max=90, size=(120,-1))
        self.bike_throttle_sensitivity = LabeledSpinCtrl(self.nb_pnl_bike, name="Throttle Sensitivity (%)", min=1, max=10000, size=(120,-1))
        self.bike_throttle_decrease_per_sec = LabeledSpinCtrl(self.nb_pnl_bike, name="Throttle Decrease per Second (%)", min=0, max=10000, size=(120,-1))
        self.nb_pnl_bike.Add(self.bike_max_lean, flag=wx.EXPAND)
        self.nb_pnl_bike.AddSpacer(PAD_sm)
        self.nb_pnl_bike.Add(self.bike_max_steer, flag=wx.EXPAND)
        self.nb_pnl_bike.AddSpacer(PAD_sm)
        self.nb_pnl_bike.Add(self.bike_throttle_sensitivity, flag=wx.EXPAND)
        self.nb_pnl_bike.AddSpacer(PAD_sm)
        self.nb_pnl_bike.Add(self.bike_throttle_decrease_per_sec, flag=wx.EXPAND)
        self.nb_pnl_bike.AddSpacer(PAD_m)
        
        self.bike_mode_absolute_radio = wx.RadioButton(self.nb_pnl_bike, name="Absolute", label="Use Absolute Positioning", style=wx.RB_GROUP)
        self.bike_mode_relative_radio = wx.RadioButton(self.nb_pnl_bike, name="Relative", label="Use Relative Positioning")

        ### Absolute box
        self.nb_pnl_bike.Add(self.bike_mode_absolute_radio)
        self.nb_pnl_bike.Add(
            HelperText(self.nb_pnl_bike, is_muted=True, label="Position of hands determines the lean angle"))
        self.nb_pnl_bike.AddSpacer(PAD_sm)

        self.bike_absolute_box = HelperPanel(self.nb_pnl_bike, FRAME_PAD, label="Absolute Mode")

        self.bike_handlebar_height = LabeledSpinCtrl(self.bike_absolute_box, name="Handlebar Height (cm)", min=50, max=300, size=(120,-1))
        self.bike_absolute_box.Add(self.bike_handlebar_height, flag=wx.EXPAND)
        self.bike_absolute_box.Add(
            HelperText(self.bike_absolute_box, is_muted=True, label="In-game bike model handlebar's height from the floor"))

        self.nb_pnl_bike.Add(self.bike_absolute_box, flag=wx.EXPAND)

        ### Relative box
        self.nb_pnl_bike.AddSpacer(PAD_m)
        self.nb_pnl_bike.Add(self.bike_mode_relative_radio)
        self.nb_pnl_bike.Add(
            HelperText(self.nb_pnl_bike, is_muted=True, label="Angle between two hands determine the lean angle"))
        self.nb_pnl_bike.AddSpacer(PAD_sm)

        self.bike_relative_box = HelperPanel(self.nb_pnl_bike, FRAME_PAD, label="Relative Mode")
        self.bike_relative_sensitivity = LabeledSpinCtrl(self.bike_relative_box, name="Relative Sensitivity (%)", min=1, max=10000, size=(120,-1))
        self.bike_relative_box.Add(self.bike_relative_sensitivity, flag=wx.EXPAND)

        self.nb_pnl_bike.Add(self.bike_relative_box, flag=wx.EXPAND)

        # BINDINGS

        # Profile binds
        self.profile_combo.Bind(wx.EVT_COMBOBOX, self.profile_change)
        self.profile_new.Bind(wx.EVT_BUTTON, self.profile_buttons)
        self.profile_delete.Bind(wx.EVT_BUTTON, self.profile_buttons)
        self.profile_open_dir.Bind(wx.EVT_BUTTON, self.profile_buttons)

        # General
        self.bind("trigger_pre_press_button", self.trigger_pre_btn_box)
        self.bind("trigger_press_button", self.trigger_btn_box)
        self.bind("multibutton_trackpad", self.multibutton_trackpad_box)
        self.bind("sfx_volume", self.sfx_volume)
        self.bind("haptic_intensity", self.haptic_intensity)

        ## Joystick button or axis
        self.bind("j_l_left_button", self.j_l_left_button)
        self.bind("j_l_right_button", self.j_l_right_button)
        self.bind("j_l_up_button", self.j_l_up_button)
        self.bind("j_l_down_button", self.j_l_down_button)
        self.bind("j_r_left_button", self.j_r_left_button)
        self.bind("j_r_right_button", self.j_r_right_button)
        self.bind("j_r_up_button", self.j_r_up_button)
        self.bind("j_r_down_button", self.j_r_down_button)
        self.bind("axis_deadzone", self.axis_deadzone)

        # Wheel
        self.bind("wheel_grabbed_by_grip", self.wheel_grabbed_by_grip_box)
        self.bind("wheel_grabbed_by_grip_toggle", self.wheel_grabbed_by_grip_box_toggle)
        self.bind("wheel_degrees", self.wheel_degrees)
        self.bind("wheel_centerforce", self.wheel_centerforce)
        self.bind("wheel_ffb", self.wheel_ffb)
        self.bind("wheel_ffb_haptic", self.wheel_ffb_haptic)
        self.bind("wheel_pitch", self.wheel_pitch)
        self.bind("wheel_alpha", self.wheel_alpha)
        self.bind("wheel_transparent_center", self.wheel_transparent_center_box)

        ## Shifter
        self.bind("shifter_degree", self.shifter_degree)
        self.bind("shifter_alpha", self.shifter_alpha)
        self.bind("shifter_scale", self.shifter_scale)
        self.bind("shifter_sequential", self.shifter_sequential)
        self.bind("shifter_reverse_orientation", [shifter_rev_tl, shifter_rev_tr, shifter_rev_bl, shifter_rev_br])

        # Bike
        self.bind("bike_show_handlebar", self.bike_show_handlebar)
        self.bind("bike_show_hands", self.bike_show_hands)
        self.bind("bike_use_ac_server", self.bike_use_ac_server)
        self.bind("bike_handlebar_height", self.bike_handlebar_height)
        self.bind("bike_max_lean", self.bike_max_lean)
        self.bind("bike_max_steer", self.bike_max_steer)
        self.bind("bike_throttle_sensitivity", self.bike_throttle_sensitivity)
        self.bind("bike_throttle_decrease_per_sec", self.bike_throttle_decrease_per_sec)
        self.bind("bike_relative_sensitivity", self.bike_relative_sensitivity)
        self.bind("bike_mode", [self.bike_mode_absolute_radio, self.bike_mode_relative_radio])

        no_binds = set(DEFAULT_CONFIG.keys()) - set(self._config_map.keys())
        #print(no_binds)

        # Fit
        for win in deferred[::-1]:
            win.Fit()

        self.window.Show(True)
        self.read_config()

    def bind(self, key, ctrl):

        self._config_map[key] = ctrl

        if is_array(ctrl):

            if all(isinstance(i, wx.RadioButton) for i in ctrl):
                for each in ctrl:
                    each.Bind(wx.EVT_RADIOBUTTON, self.config_change)
            else:
                raise ValueError("Control type not supported")

        elif isinstance(ctrl, wx.SpinCtrl):
            ctrl.Bind(wx.EVT_SPINCTRL, self.config_change)
        elif isinstance(ctrl, wx.SpinCtrlDouble):
            ctrl.Bind(wx.EVT_SPINCTRLDOUBLE, self.config_change)
        elif isinstance(ctrl, LabeledSpinCtrl):
            if ctrl.is_double:
                ctrl.Bind(wx.EVT_SPINCTRLDOUBLE, self.config_change)
            else:
                ctrl.Bind(wx.EVT_SPINCTRL, self.config_change)
        elif isinstance(ctrl, wx.CheckBox):
            ctrl.Bind(wx.EVT_CHECKBOX, self.config_change)
        elif isinstance(ctrl, wx.RadioBox):
            ctrl.Bind(wx.EVT_RADIOBOX, self.config_change)
        else:
            raise ValueError("Control type not supported")

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
        self.profile_combo.Append("(Default)")
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

            try:
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

            except KeyError:
                print(f"'{key}' is not found in self.config._data")

            except AttributeError:
                print(f"'{key}' is not found in attributes of self.config")


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
        p = cb.GetValue()
        if p == "(Default)":
            self.config._load_default()
            cb.SetValue("")
        else:
            self.config.switch_profile(p)
        self.read_config()

    def profile_buttons(self, event):
        l = event.GetEventObject()
        if l == self.profile_new:

            fd = wx.FileDialog(self.pnl, "Save Profile",
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

        elif l == self.profile_delete:
            i = self.profile_combo.GetSelection()
            if i != wx.NOT_FOUND:
                self.config.delete_profile(self.profile_combo.GetValue())
                self.profile_combo.Delete(i)
        elif l == self.profile_open_dir:
            os.startfile(self.config.get_config_dir())

    def run(self):
        self.app.MainLoop()



def run():
    ConfiguratorApp().run()

if __name__ == '__main__':
    run()