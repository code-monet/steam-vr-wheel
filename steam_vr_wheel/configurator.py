import sys
import wx
import os

from steam_vr_wheel import PadConfig, ConfigException, DEFAULT_CONFIG
from steam_vr_wheel.util import expand_to_array, is_array
from steam_vr_wheel.i18n import _I


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
        wrap_hbox.Add(inner, proportion=1, flag=wx.ALIGN_CENTER)
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

        #label = "\n".join(a.strip() for a in label.split("\n"))

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
        pnl_spin = wx.Panel(self)
        pnl_spin_sizer = wx.BoxSizer(wx.VERTICAL)
        self.is_double = is_double
        if is_double:
            self.spin = wx.SpinCtrlDouble(pnl_spin, size=(120, -1), *args, **kwargs)
            self.spin.SetDigits(1)
        else:
            self.spin = wx.SpinCtrl(pnl_spin, size=(120, -1), *args, **kwargs)

        # Center align
        label_height = label.GetBestSize()[1]
        spin_height = self.spin.GetBestSize()[1]
        pnl_label_sizer.AddSpacer(1 + int((spin_height - label_height) / 2))
        pnl_label_sizer.Add(label, flag=wx.ALIGN_RIGHT)
        pnl_label.SetSizerAndFit(pnl_label_sizer)

        #
        pnl_spin_sizer.Add(self.spin, flag=wx.ALIGN_CENTER)
        pnl_spin.SetSizerAndFit(pnl_spin_sizer)

        # Add the label, with proportion=1 so it expands horizontally.
        sizer.Add(pnl_label, proportion=1, flag=wx.EXPAND | wx.ALL)

        # Add the spin control with fixed size.
        sizer.Add(pnl_spin, proportion=1, flag=wx.EXPAND | wx.ALL)
        sizer.AddSpacer(60)
        
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
PAGE_PAD = (16, 12, 30, 12)
FRAME_PAD = (12, 8, 16, 8)

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

        self.pnl = HelperPanel(self.window, (10, 12, 16, 12), size=(500, -1))
        defer_fit(self.pnl)

        self.nb_advanced_pages = []

        #
        self.pnl.AddSpacer(PAD_m)

        pnl_header = HelperPanel(self.pnl, (0, PAD_sm * 2))
        self.pnl.Add(pnl_header, flag=wx.EXPAND)

        pnl_header.Add(wx.StaticText(pnl_header, label=_I("{cfg.selected_profile}")))

        pnl_profile_buttons = HelperPanel(pnl_header, vertical=False)
        pnl_header.Add(pnl_profile_buttons, flag=wx.EXPAND)

        self.profile_combo = wx.ComboBox(pnl_profile_buttons, style=wx.CB_READONLY, size=(160,24))
        pnl_profile_buttons.Add(self.profile_combo)
        pnl_profile_buttons.AddSpacer(6)

        self.profile_new = wx.Button(pnl_profile_buttons, label=_I('{cfg.save}'), size=(60,22))
        self.profile_open_dir = wx.Button(pnl_profile_buttons, label=_I('{cfg.open_dir}'), size=(60,22))
        self.profile_delete = wx.Button(pnl_profile_buttons, label=_I('{cfg.delete}'), size=(60,22))
        pnl_profile_buttons.Add(self.profile_new)
        pnl_profile_buttons.Add(self.profile_open_dir)
        pnl_profile_buttons.Add(self.profile_delete)

        pnl_header.AddSpacer(PAD_lg)

        pnl_general = HelperPanel(pnl_header, FRAME_PAD, label=_I('cfg.general'))
        pnl_header.Add(pnl_general, flag=wx.EXPAND)

        trigger_pre_btn_box = wx.CheckBox(pnl_general, label=_I('cfg.trigger_pre_btn_box'))
        trigger_btn_box = wx.CheckBox(pnl_general, label=_I('cfg.trigger_btn_box'))
        pnl_general.Add(trigger_pre_btn_box)
        pnl_general.Add(trigger_btn_box)

        pnl_general.AddSpacer(PAD_m)

        sfx_volume = LabeledSpinCtrl(pnl_general, name=_I('cfg.sfx_volume'), min=0, max=100)
        pnl_general.Add(sfx_volume, flag=wx.EXPAND)
        pnl_general.AddSpacer(PAD_sm)
        haptic_intensity = LabeledSpinCtrl(pnl_general, name=_I('cfg.haptic_intensity'), min=0, max=200)
        pnl_general.Add(haptic_intensity, flag=wx.EXPAND)

        self.pnl.AddSpacer(PAD_m)

        ## Joystick button or axis

        nb = wx.Notebook(self.pnl, style=wx.NB_MULTILINE)
        self.nb = nb
        self.pnl.Add(nb, flag=wx.EXPAND)

        ## Joystick page
        nb_pnl_joystick = HelperPanel(nb, PAGE_PAD)
        nb.AddPage(nb_pnl_joystick, _I(" {cfg.joystick} "))

        axis_deadzone = LabeledSpinCtrl(nb_pnl_joystick, name=_I('cfg.axis_deadzone'), min=0, max=100)
        nb_pnl_joystick.Add(axis_deadzone, flag=wx.EXPAND)
        nb_pnl_joystick.AddSpacer(PAD_xl)
        
        pnl_joystick_frame = HelperPanel(nb_pnl_joystick, FRAME_PAD, label=_I('cfg.pnl_joystick_frame'))
        nb_pnl_joystick.Add(pnl_joystick_frame, flag=wx.EXPAND)

        pnl_joystick_frame.Add(HelperText(pnl_joystick_frame, is_muted=True, label=_I('cfg.pnl_joystick_frame_descr')))
        pnl_joystick_frame.AddSpacer(PAD_m)

        pnl_joystick = HelperPanel(pnl_joystick_frame, vertical=False)
        pnl_joystick_frame.Add(pnl_joystick, flag=wx.EXPAND)

        j_l_left_button = wx.CheckBox(pnl_joystick, label='L ◀')
        j_l_right_button = wx.CheckBox(pnl_joystick, label='L ▶')
        j_l_up_button = wx.CheckBox(pnl_joystick, label='L ▲')
        j_l_down_button = wx.CheckBox(pnl_joystick, label='L ▼')
        j_r_left_button = wx.CheckBox(pnl_joystick, label='R ◀')
        j_r_right_button = wx.CheckBox(pnl_joystick, label='R ▶')
        j_r_up_button = wx.CheckBox(pnl_joystick, label='R ▲')
        j_r_down_button = wx.CheckBox(pnl_joystick, label='R ▼')
        pnl_joystick.Add(j_l_left_button); pnl_joystick.AddSpacer(6)
        pnl_joystick.Add(j_l_right_button); pnl_joystick.AddSpacer(6)
        pnl_joystick.Add(j_l_up_button); pnl_joystick.AddSpacer(6)
        pnl_joystick.Add(j_l_down_button); pnl_joystick.AddSpacer(6)
        pnl_joystick.Add(j_r_left_button); pnl_joystick.AddSpacer(6)
        pnl_joystick.Add(j_r_right_button); pnl_joystick.AddSpacer(6)
        pnl_joystick.Add(j_r_up_button); pnl_joystick.AddSpacer(6)
        pnl_joystick.Add(j_r_down_button)

        nb_pnl_joystick.AddSpacer(PAD_xl)
        multibutton_trackpad_box = wx.CheckBox(nb_pnl_joystick, label=_I('cfg.multibutton_trackpad_box'))
        nb_pnl_joystick.Add(multibutton_trackpad_box)
        nb_pnl_joystick.AddSpacer(PAD_sm)
        nb_pnl_joystick.Add(HelperText(nb_pnl_joystick, 
            is_muted=True,
            label=_I('cfg.multibutton_trackpad_box_descr')))

        ## Wheel Page
        nb_pnl_wheel = HelperPanel(nb, PAGE_PAD)
        nb.AddPage(nb_pnl_wheel, _I(" {cfg.wheel} "))

        wheel_degrees = LabeledSpinCtrl(nb_pnl_wheel, name=_I("cfg.wheel_degrees"), max=10000)
        nb_pnl_wheel.Add(wheel_degrees, flag=wx.EXPAND)
        nb_pnl_wheel.AddSpacer(PAD_sm)
        nb_pnl_wheel.Add(
            HelperText(nb_pnl_wheel, is_muted=True, label=_I('{cfg.wheel_degrees_descr}  ')),
            flag=wx.ALIGN_CENTER)
        nb_pnl_wheel.AddSpacer(PAD_xl)

        wheel_pitch = LabeledSpinCtrl(nb_pnl_wheel, name=_I('cfg.wheel_pitch'), min=-30, max=120)
        nb_pnl_wheel.Add(wheel_pitch, flag=wx.EXPAND)
        nb_pnl_wheel.AddSpacer(PAD_sm)

        wheel_alpha = LabeledSpinCtrl(nb_pnl_wheel, name=_I('cfg.wheel_alpha'), max=100)
        wheel_transparent_center_box = wx.CheckBox(nb_pnl_wheel, label=_I('cfg.wheel_transparent_center_box'))
        nb_pnl_wheel.Add(wheel_alpha, flag=wx.EXPAND)
        nb_pnl_wheel.AddSpacer(PAD_sm)
        nb_pnl_wheel.Add(wheel_transparent_center_box)
        nb_pnl_wheel.AddSpacer(PAD_xl)

        wheel_centering = HelperPanel(nb_pnl_wheel, FRAME_PAD, label=_I('cfg.wheel_centering'))
        nb_pnl_wheel.Add(wheel_centering, flag=wx.EXPAND)

        wheel_centerforce = LabeledSpinCtrl(wheel_centering, name=_I('cfg.wheel_centerforce') , max=10000)
        wheel_ffb = wx.CheckBox(wheel_centering, label=_I('cfg.wheel_ffb'))
        wheel_ffb_haptic = wx.CheckBox(wheel_centering, label=_I('cfg.wheel_ffb_haptic'))
        wheel_centering.Add(wheel_centerforce, flag=wx.EXPAND)
        wheel_centering.AddSpacer(PAD_lg)
        wheel_centering.Add(wheel_ffb)
        wheel_centering.Add(wheel_ffb_haptic)
        nb_pnl_wheel.AddSpacer(PAD_xl)

        wheel_grab_behavior = HelperPanel(nb_pnl_wheel, FRAME_PAD, label=_I('cfg.wheel_grab_behavior'))
        nb_pnl_wheel.Add(wheel_grab_behavior, flag=wx.EXPAND)

        wheel_grabbed_by_grip_box = wx.CheckBox(wheel_grab_behavior, label=_I('cfg.wheel_grabbed_by_grip_box'))
        wheel_grabbed_by_grip_box_toggle = wx.CheckBox(wheel_grab_behavior, label=_I('cfg.wheel_grabbed_by_grip_box_toggle'))
        wheel_grab_behavior.Add(wheel_grabbed_by_grip_box)
        wheel_grab_behavior.Add(wheel_grabbed_by_grip_box_toggle)

        ## Shifter page
        nb_pnl_shifter = HelperPanel(nb, PAGE_PAD)
        nb.AddPage(nb_pnl_shifter, _I(" {cfg.shifter} "))

        shifter_degree = LabeledSpinCtrl(nb_pnl_shifter, is_double=True, name=_I('cfg.shifter_degree'), \
            inc=0.1, min=0.0, max=30.0)
        nb_pnl_shifter.Add(shifter_degree, flag=wx.EXPAND)
        nb_pnl_shifter.AddSpacer(PAD_sm)

        shifter_alpha = LabeledSpinCtrl(nb_pnl_shifter, name=_I('cfg.shifter_alpha'), min=0, max=100)
        nb_pnl_shifter.Add(shifter_alpha, flag=wx.EXPAND)
        nb_pnl_shifter.AddSpacer(PAD_sm)

        shifter_scale = LabeledSpinCtrl(nb_pnl_shifter, name=_I('cfg.shifter_scale'), min=10, max=100)
        nb_pnl_shifter.Add(shifter_scale, flag=wx.EXPAND)
        nb_pnl_shifter.AddSpacer(PAD_sm)
        nb_pnl_shifter.Add(
            HelperText(nb_pnl_shifter, is_muted=True, label=_I('{cfg.shifter_scale_descr}  ')),
            flag=wx.ALIGN_CENTER)
        nb_pnl_shifter.AddSpacer(PAD_xl)
        
        shifter_sequential = wx.CheckBox(nb_pnl_shifter, label=_I('cfg.shifter_sequential'))
        nb_pnl_shifter.Add(shifter_sequential)
        nb_pnl_shifter.AddSpacer(PAD_xl)

        shifter_rev = HelperPanel(nb_pnl_shifter, FRAME_PAD, vertical=False, label=_I('cfg.shifter_rev'))
        nb_pnl_shifter.Add(shifter_rev, flag=wx.EXPAND)

        shifter_rev_tl = wx.RadioButton(shifter_rev, name="Top Left", label=_I('cfg.shifter_rev_tl'), style=wx.RB_GROUP)
        shifter_rev_tr = wx.RadioButton(shifter_rev, name="Top Right", label=_I('cfg.shifter_rev_tr'))
        shifter_rev_bl = wx.RadioButton(shifter_rev, name="Bottom Left", label=_I('cfg.shifter_rev_bl'))
        shifter_rev_br = wx.RadioButton(shifter_rev, name="Bottom Right", label=_I('cfg.shifter_rev_br'))
        shifter_rev.Add(shifter_rev_tl); shifter_rev.AddSpacer(6)
        shifter_rev.Add(shifter_rev_tr); shifter_rev.AddSpacer(6)
        shifter_rev.Add(shifter_rev_bl); shifter_rev.AddSpacer(6)
        shifter_rev.Add(shifter_rev_br)

        ## Bike page
        nb_pnl_bike = HelperPanel(nb, PAGE_PAD)
        nb.AddPage(nb_pnl_bike, _I(" {cfg.bike} "))
        self.nb_advanced_pages.append([nb_pnl_bike, _I(" {cfg.bike} ")])

        bike_show_handlebar = wx.CheckBox(nb_pnl_bike, label=_I('cfg.bike_show_handlebar'))
        bike_show_hands = wx.CheckBox(nb_pnl_bike, label=_I('cfg.bike_show_hands'))
        bike_use_ac_server = wx.CheckBox(nb_pnl_bike, label=_I('cfg.bike_use_ac_server'))
        nb_pnl_bike.Add(bike_show_handlebar)
        nb_pnl_bike.Add(bike_show_hands)
        nb_pnl_bike.Add(bike_use_ac_server)
        nb_pnl_bike.AddSpacer(PAD_sm)

        bike_max_lean = LabeledSpinCtrl(nb_pnl_bike, name=_I('cfg.bike_max_lean'), min=0, max=90)
        bike_max_steer = LabeledSpinCtrl(nb_pnl_bike, name=_I('cfg.bike_max_steer'), min=0, max=90)
        bike_throttle_sensitivity = LabeledSpinCtrl(nb_pnl_bike, name=_I('cfg.bike_throttle_sensitivity'), min=1, max=10000)
        bike_throttle_decrease_per_sec = LabeledSpinCtrl(nb_pnl_bike, name=_I('cfg.bike_throttle_decrease_per_sec'), min=0, max=10000)
        nb_pnl_bike.Add(bike_max_lean, flag=wx.EXPAND)
        nb_pnl_bike.AddSpacer(PAD_sm)
        nb_pnl_bike.Add(bike_max_steer, flag=wx.EXPAND)
        nb_pnl_bike.AddSpacer(PAD_sm)
        nb_pnl_bike.Add(bike_throttle_sensitivity, flag=wx.EXPAND)
        nb_pnl_bike.AddSpacer(PAD_sm)
        nb_pnl_bike.Add(bike_throttle_decrease_per_sec, flag=wx.EXPAND)
        nb_pnl_bike.AddSpacer(PAD_m)
        
        bike_mode_absolute_radio = wx.RadioButton(nb_pnl_bike, name="Absolute", label=_I('cfg.bike_mode_absolute_radio'), style=wx.RB_GROUP)
        bike_mode_relative_radio = wx.RadioButton(nb_pnl_bike, name="Relative", label=_I('cfg.bike_mode_relative_radio'))

        ### Absolute box
        nb_pnl_bike.Add(bike_mode_absolute_radio)
        nb_pnl_bike.AddSpacer(PAD_sm)
        nb_pnl_bike.Add(
            HelperText(nb_pnl_bike, is_muted=True, label=_I('cfg.bike_mode_absolute_radio_descr')))
        nb_pnl_bike.AddSpacer(PAD_sm)

        bike_absolute_box = HelperPanel(nb_pnl_bike, FRAME_PAD, label=_I('cfg.bike_absolute_box'))

        bike_handlebar_height = LabeledSpinCtrl(bike_absolute_box, name=_I('cfg.bike_handlebar_height'), min=50, max=300)
        bike_absolute_box.Add(bike_handlebar_height, flag=wx.EXPAND)
        bike_absolute_box.AddSpacer(PAD_sm)
        bike_absolute_box.Add(
            HelperText(bike_absolute_box, is_muted=True, label=_I('cfg.bike_handlebar_height_descr')))

        nb_pnl_bike.Add(bike_absolute_box, flag=wx.EXPAND)

        ### Relative box
        nb_pnl_bike.AddSpacer(PAD_m)
        nb_pnl_bike.Add(bike_mode_relative_radio)
        nb_pnl_bike.AddSpacer(PAD_sm)
        nb_pnl_bike.Add(
            HelperText(nb_pnl_bike, is_muted=True, label=_I('cfg.bike_mode_relative_radio_descr')))
        nb_pnl_bike.AddSpacer(PAD_sm)

        bike_relative_box = HelperPanel(nb_pnl_bike, FRAME_PAD, label=_I('cfg.bike_relative_box'))
        bike_relative_sensitivity = LabeledSpinCtrl(bike_relative_box, name=_I('cfg.bike_relative_sensitivity'), min=1, max=10000)
        bike_relative_box.Add(bike_relative_sensitivity, flag=wx.EXPAND)

        nb_pnl_bike.Add(bike_relative_box, flag=wx.EXPAND)

        # Advanced
        self.pnl.AddSpacer(PAD_sm * 2)
        advanced_mode = wx.CheckBox(self.pnl, label=_I("cfg.advanced_mode"))
        self.advanced_mode = advanced_mode
        self.pnl.Add(advanced_mode, flag=wx.ALIGN_RIGHT)

        ## Advanced page
        nb_pnl_advanced = HelperPanel(nb, PAGE_PAD)
        nb.AddPage(nb_pnl_advanced, _I(" {cfg.advanced} "))
        self.nb_advanced_pages.append([nb_pnl_advanced, _I(" {cfg.advanced} ")])

        nb_pnl_advanced.Add(
            HelperText(nb_pnl_advanced, is_muted=True, label=_I('cfg.advanced_descr')),
            flag=wx.ALIGN_CENTER)
        nb_pnl_advanced.AddSpacer(PAD_m)
        adv_vjoy_device = LabeledSpinCtrl(nb_pnl_advanced, name='adv_vjoy_device', min=1, max=16)
        nb_pnl_advanced.Add(adv_vjoy_device, flag=wx.EXPAND)
        # TODO add button constants (mapping) to advanced so that user can change
        #      the ids used for toggling splitter or range on shifter knob or other buttons ids as well

        # BINDINGS

        # Profile binds
        self.profile_combo.Bind(wx.EVT_COMBOBOX, self.profile_change)
        self.profile_new.Bind(wx.EVT_BUTTON, self.profile_buttons)
        self.profile_delete.Bind(wx.EVT_BUTTON, self.profile_buttons)
        self.profile_open_dir.Bind(wx.EVT_BUTTON, self.profile_buttons)

        # General
        self.bind("trigger_pre_press_button", trigger_pre_btn_box)
        self.bind("trigger_press_button", trigger_btn_box)
        self.bind("multibutton_trackpad", multibutton_trackpad_box)
        self.bind("sfx_volume", sfx_volume)
        self.bind("haptic_intensity", haptic_intensity)

        ## Joystick button or axis
        self.bind("j_l_left_button", j_l_left_button)
        self.bind("j_l_right_button", j_l_right_button)
        self.bind("j_l_up_button", j_l_up_button)
        self.bind("j_l_down_button", j_l_down_button)
        self.bind("j_r_left_button", j_r_left_button)
        self.bind("j_r_right_button", j_r_right_button)
        self.bind("j_r_up_button", j_r_up_button)
        self.bind("j_r_down_button", j_r_down_button)
        self.bind("axis_deadzone", axis_deadzone)

        # Wheel
        self.bind("wheel_grabbed_by_grip", wheel_grabbed_by_grip_box)
        self.bind("wheel_grabbed_by_grip_toggle", wheel_grabbed_by_grip_box_toggle)
        self.bind("wheel_degrees", wheel_degrees)
        self.bind("wheel_centerforce", wheel_centerforce)
        self.bind("wheel_ffb", wheel_ffb)
        self.bind("wheel_ffb_haptic", wheel_ffb_haptic)
        self.bind("wheel_pitch", wheel_pitch)
        self.bind("wheel_alpha", wheel_alpha)
        self.bind("wheel_transparent_center", wheel_transparent_center_box)

        # Shifter
        self.bind("shifter_degree", shifter_degree)
        self.bind("shifter_alpha", shifter_alpha)
        self.bind("shifter_scale", shifter_scale)
        self.bind("shifter_sequential", shifter_sequential)
        self.bind("shifter_reverse_orientation", [shifter_rev_tl, shifter_rev_tr, shifter_rev_bl, shifter_rev_br])

        # Bike
        self.bind("bike_show_handlebar", bike_show_handlebar)
        self.bind("bike_show_hands", bike_show_hands)
        self.bind("bike_use_ac_server", bike_use_ac_server)
        self.bind("bike_handlebar_height", bike_handlebar_height)
        self.bind("bike_max_lean", bike_max_lean)
        self.bind("bike_max_steer", bike_max_steer)
        self.bind("bike_throttle_sensitivity", bike_throttle_sensitivity)
        self.bind("bike_throttle_decrease_per_sec", bike_throttle_decrease_per_sec)
        self.bind("bike_relative_sensitivity", bike_relative_sensitivity)
        self.bind("bike_mode", [bike_mode_absolute_radio, bike_mode_relative_radio])

        # Advanced
        self.bind("advanced_mode", advanced_mode)
        self.bind("adv_vjoy_device", adv_vjoy_device)

        no_binds = set(DEFAULT_CONFIG.keys()) - set(self._config_map.keys())
        #print(no_binds)

        # Fit
        for win in deferred[::-1]:
            win.Fit()

        self.window.Show(True)
        self.read_config()

        # Bind advanced mode
        self.read_advanced_mode()
        advanced_mode.Bind(wx.EVT_CHECKBOX, self.on_advanced_mode)

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

    def on_advanced_mode(self, event):
        self.read_advanced_mode()
        event.Skip()

    def read_advanced_mode(self):
        on = self.advanced_mode.GetValue()

        for page, label in self.nb_advanced_pages:
            i = self.nb.FindPage(page)
            if on == True and i == wx.NOT_FOUND:
                self.nb.AddPage(page, label)
            elif on == False:
                self.nb.RemovePage(i)

    def read_config(self):
        try:
            self.config = PadConfig()
            
        except FileNotFoundError:
            self.config = PadConfig(load_defaults=True)

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
        event.Skip()

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