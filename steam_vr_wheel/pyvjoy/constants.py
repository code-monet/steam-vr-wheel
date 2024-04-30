from enum import Enum

DLL_FILENAME = "vJoyInterface.dll"

HID_USAGE_X = 0x30
HID_USAGE_Y	= 0x31
HID_USAGE_Z	= 0x32
HID_USAGE_RX = 0x33
HID_USAGE_RY = 0x34
HID_USAGE_RZ = 0x35
HID_USAGE_SL0 = 0x36
HID_USAGE_SL1 = 0x37
HID_USAGE_WHL = 0x38
HID_USAGE_POV = 0x39

#for validity checking
HID_USAGE_LOW = HID_USAGE_X
HID_USAGE_HIGH = HID_USAGE_POV


VJD_STAT_OWN = 0	# The  vJoy Device is owned by this application.
VJD_STAT_FREE = 1 	# The  vJoy Device is NOT owned by any application (including this one).
VJD_STAT_BUSY = 2   # The  vJoy Device is owned by another application. It cannot be acquired by this application.
VJD_STAT_MISS = 3 	# The  vJoy Device is missing. It either does not exist or the driver is down.
VJD_STAT_UNKN = 4 	# Unknown



# FFB
ERROR_SUCCESS = 0x0
ERROR_INVALID_PARAMETER = 0x57
ERROR_INVALID_DATA = 0xd

## HID Descriptor definitions - FFB Effects
HID_USAGE_CONST = 0x26 #    Usage ET Constant Force
HID_USAGE_RAMP = 0x27 #    Usage ET Ramp
HID_USAGE_SQUR = 0x30 #    Usage ET Square
HID_USAGE_SINE = 0x31 #    Usage ET Sine
HID_USAGE_TRNG = 0x32 #    Usage ET Triangle
HID_USAGE_STUP = 0x33 #    Usage ET Sawtooth Up
HID_USAGE_STDN = 0x34 #    Usage ET Sawtooth Down
HID_USAGE_SPRNG = 0x40 #    Usage ET Spring
HID_USAGE_DMPR = 0x41 #    Usage ET Damper
HID_USAGE_INRT = 0x42 #    Usage ET Inertia
HID_USAGE_FRIC = 0x43 #    Usage ET Friction

## HID Descriptor definitions - FFB Report IDs
HID_ID_STATE = 0x02 # Usage PID State report
HID_ID_EFFREP = 0x01 # Usage Set Effect Report
HID_ID_ENVREP = 0x02 # Usage Set Envelope Report
HID_ID_CONDREP = 0x03 # Usage Set Condition Report
HID_ID_PRIDREP = 0x04 # Usage Set Periodic Report
HID_ID_CONSTREP = 0x05 # Usage Set Constant Force Report
HID_ID_RAMPREP = 0x06 # Usage Set Ramp Force Report
HID_ID_CSTMREP = 0x07 # Usage Custom Force Data Report
HID_ID_SMPLREP = 0x08 # Usage Download Force Sample
HID_ID_EFOPREP = 0x0A # Usage Effect Operation Report
HID_ID_BLKFRREP = 0x0B # Usage PID Block Free Report
HID_ID_CTRLREP = 0x0C # Usage PID Device Control
HID_ID_GAINREP = 0x0D # Usage Device Gain Report
HID_ID_SETCREP = 0x0E # Usage Set Custom Force Report
HID_ID_NEWEFREP = 0x01 # Usage Create New Effect Report
HID_ID_BLKLDREP = 0x02 # Usage Block Load Report
HID_ID_POOLREP = 0x03 # Usage PID Pool Report

class FFBEType(Enum):
	ET_NONE = 0
	ET_CONST = 1
	ET_RAMP = 2
	ET_SQR = 3
	ET_SINE = 4
	ET_TRNGL = 5
	ET_STUP = 6
	ET_STDN = 7
	ET_SPRNG = 8
	ET_DMPR = 9
	ET_INRT = 10
	ET_FRCTN = 11
	ET_CSTM = 12

class FFBPType(Enum):
	# Write
	PT_EFFREP	=  HID_ID_EFFREP 	# Usage Set Effect Report
	PT_ENVREP	=  HID_ID_ENVREP 	# Usage Set Envelope Report
	PT_CONDREP	=  HID_ID_CONDREP 	# Usage Set Condition Report
	PT_PRIDREP	=  HID_ID_PRIDREP 	# Usage Set Periodic Report
	PT_CONSTREP	=  HID_ID_CONSTREP 	# Usage Set Constant Force Report
	PT_RAMPREP	=  HID_ID_RAMPREP 	# Usage Set Ramp Force Report
	PT_CSTMREP	=  HID_ID_CSTMREP 	# Usage Custom Force Data Report
	PT_SMPLREP	=  HID_ID_SMPLREP 	# Usage Download Force Sample
	PT_EFOPREP	=  HID_ID_EFOPREP 	# Usage Effect Operation Report
	PT_BLKFRREP	=  HID_ID_BLKFRREP 	# Usage PID Block Free Report
	PT_CTRLREP	=  HID_ID_CTRLREP 	# Usage PID Device Control
	PT_GAINREP	=  HID_ID_GAINREP 	# Usage Device Gain Report
	PT_SETCREP	=  HID_ID_SETCREP 	# Usage Set Custom Force Report

	# Feature
	PT_NEWEFREP	=  HID_ID_NEWEFREP+0x10 	# Usage Create New Effect Report
	PT_BLKLDREP	=  HID_ID_BLKLDREP+0x10 	# Usage Block Load Report
	PT_POOLREP	=  HID_ID_POOLREP+0x10 		# Usage PID Pool Report

class FFBOP(Enum):
	EFF_START = 1
	EFF_SOLO = 2
	EFF_STOP = 3

class FFB_CTRL(Enum):
	CTRL_ENACT = 1
	CTRL_DISACT = 2
	CTRL_STOPALL = 3
	CTRL_DEVRST = 4
	CTRL_DEVPAUSE = 5
	CTRL_DEVCONT = 6

class FFB_EFFECTS(Enum):
	Constant	= 0x0001
	Ramp		= 0x0002
	Square		= 0x0004
	Sine		= 0x0008
	Triangle	= 0x0010
	Sawtooth_Up = 0x0020
	Sawtooth_Dn = 0x0040
	Spring		= 0x0080
	Damper		= 0x0100
	Inertia		= 0x0200
	Friction	= 0x0400
	Custom		= 0x0800