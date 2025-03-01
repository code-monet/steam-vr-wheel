
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

# https://github.com/jshafer817/vJoy/blob/v2.1.9.1/apps/common/vJoyInterfaceCS/vJoyInterfaceWrap/Wrapper.cs#L57
class FFBEType:
	ET_NONE		=	0,	  # No Force
	ET_CONST	=	1,    # Constant Force
	ET_RAMP		=	2,    # Ramp
	ET_SQR		=	3,    # Square
	ET_SINE		=	4,    # Sine
	ET_TRNGL	=	5,    # Triangle
	ET_STUP		=	6,    # Sawtooth Up
	ET_STDN		=	7,    # Sawtooth Down
	ET_SPRNG	=	8,    # Spring
	ET_DMPR		=	9,    # Damper
	ET_INRT		=	10,   # Inertia
	ET_FRCTN	=	11,   # Friction
	ET_CSTM		=	12,   # Custom Force Data

class FFBPType:
	# Write
	PT_EFFREP	=  HID_ID_EFFREP 	# Usage Set Effect Report					1
	PT_ENVREP	=  HID_ID_ENVREP 	# Usage Set Envelope Report					2
	PT_CONDREP	=  HID_ID_CONDREP 	# Usage Set Condition Report				3
	PT_PRIDREP	=  HID_ID_PRIDREP 	# Usage Set Periodic Report					4
	PT_CONSTREP	=  HID_ID_CONSTREP 	# Usage Set Constant Force Report			5
	PT_RAMPREP	=  HID_ID_RAMPREP 	# Usage Set Ramp Force Report				6
	PT_CSTMREP	=  HID_ID_CSTMREP 	# Usage Custom Force Data Report			7
	PT_SMPLREP	=  HID_ID_SMPLREP 	# Usage Download Force Sample				8
	PT_EFOPREP	=  HID_ID_EFOPREP 	# Usage Effect Operation Report				10
	PT_BLKFRREP	=  HID_ID_BLKFRREP 	# Usage PID Block Free Report				11
	PT_CTRLREP	=  HID_ID_CTRLREP 	# Usage PID Device Control					12
	PT_GAINREP	=  HID_ID_GAINREP 	# Usage Device Gain Report					13
	PT_SETCREP	=  HID_ID_SETCREP 	# Usage Set Custom Force Report				14

	# Feature
	PT_NEWEFREP	=  HID_ID_NEWEFREP+0x10 	# Usage Create New Effect Report	17
	PT_BLKLDREP	=  HID_ID_BLKLDREP+0x10 	# Usage Block Load Report			18
	PT_POOLREP	=  HID_ID_POOLREP+0x10 		# Usage PID Pool Report				19

class FFBOP:
	EFF_START = 1
	EFF_SOLO  = 2 # EFFECT SOLO START
	EFF_STOP  = 3

class FFB_CTRL:
	CTRL_ENACT		= 1	# Enable all device actuators.
	CTRL_DISACT		= 2	# Disable all the device actuators.
	CTRL_STOPALL	= 3	# Stop All Effects­ Issues a stop on every running effect.
	CTRL_DEVRST		= 4	# Device Reset– Clears any device paused condition, enables all actuators and clears all effects from memory.
	CTRL_DEVPAUSE	= 5	# Device Pause– The all effects on the device are paused at the current time step.
	CTRL_DEVCONT	= 6	# Device Continue– The all effects that running when the device was paused are restarted from their last time step.

class FFB_EFFECTS:
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