from syncmrt.hardware.motor import motor
from syncmrt.widgets import QEMotor
import numpy as np

class stage:
	def __init__(self,motorList,ui=None):
		# Information
		self._name = None
		self._dof = (0,[0,0,0,0,0,0])
		self.motors = []
		# A preloadable motion.
		self._motion = None
		# Stage size information.
		self._size = np.array([0,0,0])
		# Calibration object size.
		self._offset = np.array([0,0,0])
		# UI elements.
		self._ui = ui

		# Get stagelist and motors.
		import csv, os
		# Open CSV file.
		f = open(os.path.join(os.path.dirname(__file__),motorList))
		r = csv.DictReader(f)
		# Save as ordered dict.
		self.motorList = []
		for row in r:
			self.motorList.append(row)
		# Remove the description row.
		del self.motorList[0]

	def load(self,stage,calibrationDist):
		# Remove all motors.
		for item in self.motors:
			del item
		# Set calibration values.
		self._dcal = calibrationDist
		# Iterate over new motors.
		for description in self.motorList:
			# Does the motor match the stage?
			if description['Stage'] == stage:
				# Decide kwargs based on whether the stage uses a global or local coordinate system.
				if int(description['StageLocation']) == 0:
					kwargs = {
						'pv':description['PV'],
						'direction':int(description['Direction']),
						'frame':int(description['Frame']),
						'size':[int(description['SizeX']),int(description['SizeY']),int(description['SizeZ'])],
						'workDistance':[int(description['WorkDistanceX']),int(description['WorkDistanceY']),int(description['WorkDistanceZ'])]
						'stageLocation':int(description['StageLocation'])
					}
				else:
					kwargs = {
						'pv':description['PV'],
						'direction':int(description['Direction']),
						'frame':int(description['Frame']),
					}	
				# Define the new motor.
				newMotor = motor(int(description['Axis']),
							int(description['Type']),
							int(description['Order']),
							**(kwargs))
				# Set a ui for the motor if we are doing that.
				if self._ui is not None:
					newMotor.setUi(self._ui)
				# Append the motor to the list.
				self.motors.append(newMotor)
		# Set the order of the list from 0-i.
		self.motors = sorted(self.motors, key=lambda k: k['Order']) 
		# Update the stage details.
		self._name = stage
		# Stage size in mm including calibration offset (i.e. a pin or object used to calibrate the stage).
		self._size = self._offset
		for motor in self.motors:
			if motor._stage == 0:
				self._size = np.sum(self._size,motor._size)

		# Update GUI.
		if self._ui is not None:
			self._ui.update()

	def shiftPosition(self,position):
		# This is a relative position change.
		# Iterate through available motors.
		for motor in self.motors:
			# Get position to move to for that motor.
			value = position[(motor._axis + (3*motor._type))]
			# Tell motor to shift position by amount, value.
			motor.shiftPosition(value)
			# Set position variable to 0 (if motor was successful).
			position[(motor._axis + (3*motor._type))] = 0

	def setPosition(self,position):
		# This is a direct position change.
		# Iterate through available motors.
		for motor in self.motors:
			# Get position to move to for that motor.
			value = position[(motor._axis + (3*motor._type))]
			# Tell motor to shift position by amount, value.
			motor.setPosition(value)
			# Set position variable to 0 (if motor was successful).
			position[(motor._axis + (3*motor._type))] = 0

	def position(self,idx=None):
		# return the current position of the stage in Global XYZ.
		pos = np.array([0,0,0])
		for motor in self.motors:
			if motor._stage == 1:
				# Read motor position and the axis it works on.
				mpos = motor.readPosition()
				axis = motor._axis
				# Add value to the overall position.
				pos[axis] += mpos

		# Return the position.
		if idx is not None:
			return pos[idx]
		else: 
			return pos

	def calculateMotion(self,G,variables):
		# We take in the 4x4 transformation matrix G, and a list of 6 parameters (3x translations, 3x rotations).
		# Create a transform for this stage, M.
		S = np.identity(4)
		# Position of motor in stack (in mm).
		stackPos = np.array([0,0,0])
		# Iterate over each motor in order.
		for idx, motor in self.motors:
			# Get the x y z translation or rotation value.
			value = variables[(motor._axis + (3*motor._type))]
			# Take as much of this as you can if it fits within the limits of the motor!!

			# Set the taken variable to 0. This stops any future motor from taking this value.
			variables[(motor._axis + (3*motor._type))] = 0
			# Add current motor height in stack.
			if motor._stage == 0:
				stackPos += motor._size
			# If it has a working distance, update the working point.
			if sum(motor._workDistance) > 0:
				# Get the current position of the stage.
				stagePos = self.position()
				motor.calculateWorkPoint(stagePos,self._size,stackPos)
			# Get the transform for the motor.
			T = motor.transform(value)
			# Multiply the transform into the overall transform.
			print('****** MOTOR NUMBER ',idx,':')
			print('====== S:')
			print(S)
			print('====== T:')
			print(T)
			S = S@T
			print('=== Snew:')
			print(S)
		# Now we have S, a 4x4 transform that encompases all motors.
		print('****** RESULTS:')
		print('====== G:')
		print(G)
		print('====== S:')
		print(S)
		Remainder = G@np.linalg.inv(S)
		print('====== REMAINDER:')
		print(Remainder)
		t = np.array(M[:3,3]).reshape(3,)
		r = np.array(M[:3,3]).reshape(3,)


		# We must go through and divvy up the translations again, this time applying them.
		return localSolution

	def applyMotion(self,variables):
		# Iterate over each motor in order.
		for idx, motor in motors:
			# Understand the motors function.
			index = motor._axis + (3*motor._type)
			# Get the x y z translation or rotation value.
			value = variables[index]
			# Apply the value.
			motor.shiftPosition(value)
			# Set the taken variable to 0. This stops any future motor from taking this value.
			variables[index] = 0

		return

		'''
		Start with removing the rotations.
		To remove these, we need to know the shift of the P in relation to the rotation origin.
		what's left = T*M[rx]^-1
		Find working origin.
		what's left = T*M[ry]^-1
		what's left = T*M[rz]^-1
		Whats left now should only be translations.
		After removing the translations, anything left should be considered impossible for the stage to complete. This should go into a "accuracy" measurement

		Take position of stage when working distance is at the origin. homePos
		Get the working distance, workDist
		Get it's current position. currPos
		workPos = currPos + workDist (this is the point we will rotate around)
		Transform needs the workPos.
		'''