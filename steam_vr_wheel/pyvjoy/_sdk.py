import os
import sys
from ctypes import *

from .constants import *
from .exceptions import *
from ctypes import wintypes	# Makes this lib work in Python36

dll_path = os.path.dirname(__file__) + os.sep + DLL_FILENAME

try:
	_vj = cdll.LoadLibrary(dll_path)
except OSError:
	sys.exit("Unable to load vJoy SDK DLL.  Ensure that %s is present" % DLL_FILENAME)


def vJoyEnabled():
	"""Returns True if vJoy is installed and enabled"""

	result = _vj.vJoyEnabled()

	if result == 0:
		raise vJoyNotEnabledException()
	else:
		return True


def DriverMatch():
	"""Check if the version of vJoyInterface.dll and the vJoy Driver match"""
	result = _vj.DriverMatch()
	if result == 0:
		raise vJoyDriverMismatch()
	else:
		return True


def GetVJDStatus(rID):
	"""Get the status of a given vJoy Device"""

	return _vj.GetVJDStatus(rID)


def AcquireVJD(rID):
	"""Attempt to acquire a vJoy Device"""

	result = _vj.AcquireVJD(rID)
	if result == 0:
		#Check status
		status = GetVJDStatus(rID)
		if status != VJD_STAT_FREE:
			raise vJoyFailedToAcquireException("Cannot acquire vJoy Device because it is not in VJD_STAT_FREE")

		else:
			raise vJoyFailedToAcquireException()

	else:
		return True


def RelinquishVJD(rID):
	"""Relinquish control of a vJoy Device"""

	result = _vj.RelinquishVJD(rID)
	if result == 0:
		raise vJoyFailedToRelinquishException()
	else:
		return True


def SetBtn(state,rID,buttonID):
	"""Sets the state of a vJoy Button to on or off.  SetBtn(state,rID,buttonID)"""
	result = _vj.SetBtn(state,rID,buttonID)
	if result == 0:
		raise vJoyButtonException()
	else:
		return True

def SetAxis(AxisValue,rID,AxisID):
	"""Sets the value of a vJoy Axis  SetAxis(value,rID,AxisID)"""

	#TODO validate AxisID
	#TODO validate AxisValue

	result = _vj.SetAxis(AxisValue,rID,AxisID)
	if result == 0:
		#TODO raise specific exception
		raise vJoyException()
	else:
		return True




def SetDiscPov(PovValue, rID, PovID):
	"""Write Value to a given discrete POV defined in the specified VDJ"""
	if PovValue < -1 or PovValue > 3:
		raise vJoyInvalidPovValueException()

	if PovID < 1 or PovID > 4:
		raise vJoyInvalidPovIDException

	return _vj.SetDiscPov(PovValue,rID,PovID)


def SetContPov(PovValue, rID, PovID):
	"""Write Value to a given continuous POV defined in the specified VDJ"""
	if PovValue < -1 or PovValue > 35999:
		raise vJoyInvalidPovValueException()

	if PovID < 1 or PovID > 4:
		raise vJoyInvalidPovIDException

	return _vj.SetContPov(PovValue,rID,PovID)



def SetBtn(state,rID,buttonID):
	"""Sets the state of vJoy Button to on or off.  SetBtn(state,rID,buttonID)"""
	result = _vj.SetBtn(state,rID,buttonID)
	if result == 0:
		raise vJoyButtonError()
	else:
		return True


def ResetVJD(rID):
	"""Reset all axes and buttons to default for specified vJoy Device"""
	return _vj.ResetVJD(rID)


def ResetButtons(rID):
	"""Reset all buttons to default for specified vJoy Device"""
	return _vj.ResetButtons(rID)


def ResetPovs(rID):
	"""Reset all POV hats to default for specified vJoy Device"""
	return _vj.ResetPovs(rID)

	
def UpdateVJD(rID, data):
	"""Pass data for all buttons and axes to vJoy Device efficiently"""
	return _vj.UpdateVJD(rID, data)

	
def CreateDataStructure(rID):
	data = _JOYSTICK_POSITION_V2()
	data.set_defaults(rID)
	return data
	
	
class _JOYSTICK_POSITION_V2(Structure):
	_fields_ = [
	('bDevice', c_byte),
	('wThrottle', c_long),
	('wRudder', c_long),
	('wAileron', c_long),
	('wAxisX', c_long),
	('wAxisY', c_long),
	('wAxisZ', c_long),
	('wAxisXRot', c_long),
	('wAxisYRot', c_long),
	('wAxisZRot', c_long),
	('wSlider', c_long),
	('wDial', c_long),
	('wWheel', c_long),
	('wAxisVX', c_long),
	('wAxisVY', c_long),
	('wAxisVZ', c_long),
	('wAxisVBRX', c_long),
	('wAxisVRBY', c_long),
	('wAxisVRBZ', c_long),
	('lButtons', c_long), # 32 buttons: 0x00000001 means button1 is pressed, 0x80000000 -> button32 is pressed
	
	('bHats', wintypes.DWORD ),		# Lower 4 bits: HAT switch or 16-bit of continuous HAT switch
	('bHatsEx1', wintypes.DWORD ),		# Lower 4 bits: HAT switch or 16-bit of continuous HAT switch
	('bHatsEx2', wintypes.DWORD ),		# Lower 4 bits: HAT switch or 16-bit of continuous HAT switch
	('bHatsEx3', wintypes.DWORD ),		# Lower 4 bits: HAT switch or 16-bit of continuous HAT switch LONG lButtonsEx1
	
	# JOYSTICK_POSITION_V2 Extension
	
	('lButtonsEx1', c_long),	# Buttons 33-64	
	('lButtonsEx2', c_long), # Buttons 65-96
	('lButtonsEx3', c_long), # Buttons 97-128
	]
	
	def set_defaults(self, rID):
		
		self.bDevice=c_byte(rID)
		self.bHats=-1


# FFB

class FFB_DATA(Structure):
	_fields_ = [("size", c_ulong),
				("cmd", c_ulong),
				("data", POINTER(c_ubyte))]

class FFB_DIR_UNION(Union):
	_fields_ = [("Direction", c_char),
				("DirX", c_char)]

# cf. https://learn.microsoft.com/en-us/previous-versions/windows/desktop/ee416616(v=vs.85)
class FFB_EFF_REPORT(Structure):
	_anonymous_ = ("FFB_DIR_UNION",)
	_fields_ = [("EffectBlockIndex", c_char),
				("EffectType", c_uint),
				("Duration", c_ushort),
				("TrigerRpt", c_ushort),
				("SamplePrd", c_ushort),
				("Gain", c_char),
				("TrigerBtn", c_char),
				("Polar", c_bool),
				("FFB_DIR_UNION", FFB_DIR_UNION),
				("DirY", c_char)]

class FFB_EFF_OP(Structure):
	_fields_ = [("EffectBlockIndex", c_char),
				("EffectOp", c_uint),
				("LoopCount", c_char)]

class FFB_EFF_CONSTANT(Structure):
	_fields_ = [("EffectBlockIndex", c_char),
				("Magnitude", c_long)]

class FFB_EFF_RAMP(Structure):
	_fields_ = [("EffectBlockIndex", c_char),
				("Start", c_long),
				("End", c_long)]

class FFB_EFF_PERIOD(Structure):
	_fields_ = [("EffectBlockIndex", c_char),
				("Magnitude", c_ulong),
				("Offset", c_long),
				("Phase", c_ulong),
				("Period", c_ulong)]

class FFB_EFF_ENVLP(Structure):
	_fields_ = [("EffectBlockIndex", c_char),
				("AttackLevel", c_ulong),
				("FadeLevel", c_ulong),
				("AttackTime", c_ulong),
				("FadeTime", c_ulong)]

def IsDeviceFfb(rID):
	return _vj.IsDeviceFfb(rID)

def _twos_comp(val, bits):
	if (val & (1 << (bits - 1))) != 0:
		val = val - (1 << bits) 
	return val

FFB_GEN_CB = WINFUNCTYPE(None, c_void_p, c_void_p)

# cf https://github.com/jshafer817/vJoy/blob/v2.1.9.1/apps/common/vJoyInterface/vjoyinterface.h
class FfbGenCB:

	def __init__(self, pyfunc):
		self.pyfunc = pyfunc
		def f(data, userData):
			fData = cast(data, POINTER(FFB_DATA))

			pydata = dict()

			i = c_int()
			if ERROR_SUCCESS == _vj.Ffb_h_DeviceID(fData, byref(i)):
				pydata['DeviceID'] = i.value

			if ERROR_SUCCESS == _vj.Ffb_h_Type(fData, byref(i)):
				pydata['Type'] = i.value

			if ERROR_SUCCESS == _vj.Ffb_h_DevCtrl(fData, byref(i)):
				pydata['DevCtrl'] = i.value

			op = FFB_EFF_OP()
			if ERROR_SUCCESS == _vj.Ffb_h_EffOp(fData, byref(op)):
				pydata['EffOp'] = dict({
					"EffectOp": op.EffectOp,
					"LoopCount": ord(op.LoopCount),
					})

			effect = FFB_EFF_REPORT()
			if ERROR_SUCCESS == _vj.Ffb_h_Eff_Report(fData, byref(effect)):
				pydata['Eff_Report'] = dict({
					"EffectType": effect.EffectType,
					"Duration": effect.Duration,
					"TriggerRepeatInterval": effect.TrigerRpt,
					"SamplePeriod": effect.SamplePrd,
					"Gain": ord(effect.Gain),
					"TriggerButton": ord(effect.TrigerBtn),
					"Polar": True if effect.Polar == 1 else False,
					"Direction": ord(effect.Direction),
					"DirX": _twos_comp(ord(effect.DirX), 8),
					"DirY": _twos_comp(ord(effect.DirY), 8),
					})

			cnst = FFB_EFF_CONSTANT()
			if ERROR_SUCCESS == _vj.Ffb_h_Eff_Constant(fData, byref(cnst)):

				pydata['Eff_Constant'] = dict({
					"Magnitude": _twos_comp(cnst.Magnitude, 16)
					})

			prd = FFB_EFF_PERIOD()
			# cf https://learn.microsoft.com/en-us/previous-versions/windows/desktop/ee418719(v=vs.85)
			if ERROR_SUCCESS == _vj.Ffb_h_Eff_Period(fData, byref(prd)):
				pydata['Eff_Period'] = dict({
					"Magnitude": prd.Magnitude,
					"Offset": _twos_comp(prd.Offset, 16),
					"Phase": prd.Phase,
					"Period": prd.Period
					})

			self.pyfunc(pydata)
		self.cfunc = FFB_GEN_CB(f)


def FfbRegisterGenCB(pyfunc):
	cb = FfbGenCB(pyfunc)
	_vj.FfbRegisterGenCB(cb.cfunc, None)
	return cb