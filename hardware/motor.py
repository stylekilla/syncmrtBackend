from syncmrt import math
from syncmrt.epics import controls
import numpy as np

class motor:
	def __init__(self,axis,mtype,order,name,
		pv=None,
		direction=1,
		mrange=np.array([-np.inf,np.inf]),
		frame=0,
		size=np.array([0,0,0]),
		workDistance=np.array([0,0,0]),
		stageLocation=0
		):
		# Axis can be 0,1,2 to represent x,y,z.
		self._axis = axis
		# Type is 0 (translation) or 1 (rotation).
		self._type = mtype
		# Motor order.
		self._order = order
		# Motor name.
		self._name = name
		# PV Base.
		self._pv = pv
		# Direction is +1 (forward) or -1 (reverse) for natural motor movement.
		self._direction = direction
		# Frame of reference local (0) or global (1).
		self._frame = frame
		# Does it affect the stage location? No (0), Yes (1).
		self._stage = stageLocation
		# Stage size.
		self._size = size
		# Define a work point for the motor, this will be non-zero if it has a fixed mechanical working point. This is nominally the isocenter of the machine.
		self._workDistance = workDistance
		self._workPoint = np.array([0,0,0])
		# Upper and lower limits of motor movement.
		self._range = mrange
		# Interfaces (Qt and Epics).
		self._ui = None
		self._control = controls.motor(self._pv)

	def setUi(self,ui):
		# Connect user interface.
		self._ui = motor.ui(ui)

	def setPosition(self,position):
		self._control.write(position,mode='absolute')

	def shiftPosition(self,position):
		self._control.write(position,mode='relative')

	def readPosition(self):
		return self._control.read()

	def transform(self,value):
		# If we are a translation motor, return a translation transfrom.
		if self._type == 0:
			return math.transform.translation(self._axis,value)
		if self._type == 1:
			value += self._control.read()
			return math.transform.rotation(self._axis,value,self._workPoint)

	def calculateWorkPoint(self,pstage,dstage,offset):
		if self._frame == 0:
			# Find hardware specific position in stage.
			pmotor = pstage - dstage + offset
			print('pmotor:',pmotor)
			print('pstage:',pstage)
			print('dstage:',dstage)
			print('offset:',offset)
			# Find work point related to hardware.
			self._workPoint = pstage - dstage + pmotor + self._size + self._workDistance

	def setWorkPoint(self,workpoint):
		# This is useful for robotic arms that do movements in global space.
		if self._frame == 1:
			# Can only be set if work distances are zero and it is a rotation.
			self._workPoint = workpoint