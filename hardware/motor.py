from syncmrt.tools import math
from syncmrt.epics import controls
import numpy as np

class motor:
	def __init__(self,axis,mtype,
		pv=None,
		direction=1,
		workDistance=0,
		workPoint=[0,0,0],
		mrange=[-np.inf,np.inf]
		):
		# Axis can be 0,1,2 to represent x,y,z.
		self._axis = axis
		# Type is 0 (translation) or 1 (rotation).
		self._type = mtype
		# PV Base.
		self._pv = pv
		# Direction is +1 (forward) or -1 (reverse) for natural motor movement.
		self._direction = direction
		# Define a work point for the motor, this will be non-zero if it has a fixed mechanical working point. This is nominally the isocenter of the machine.
		self._workDistance = workDistance
		self._workPoint = workPoint
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
			return math.transform.rotation(self._axis,value,self._workPoint)

	def calculateWorkPoint(self,forwardTransform):
		# Use forward kinematics to find the current working point position.
		# self._workPoint = forwardTransform@self._workPoint
		return forwardTransform@self._workPoint

	def setWorkPoint(self,location):
		self._workPoint = location
		# Should also maybe set the Epics PV to 000 here.