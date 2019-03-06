from syncmrtBackend.hardware.motor import motor
from syncmrtBackend.widgets import QEMotor
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

		self.i = 0


		# Get stagelist and motors.
		import csv, os
		# Open CSV file
		f = open(motorList)
		r = csv.DictReader(f)
		# Save as ordered dict.
		self.motorList = []
		for row in r:
			self.motorList.append(row)
		# Remove the description row.
		del self.motorList[0]

	def load(self,stage):
		# Remove all motors.
		for i in range(len(self.motors)):
			del self.motors[-1]
		# Iterate over new motors.
		for description in self.motorList:
			# Does the motor match the stage?
			if description['Stage'] == stage:
				# Decide kwargs based on whether the stage uses a global or local coordinate system.
				if (int(description['Frame']) == 0) | (int(description['StageLocation']) == 0):
					kwargs = {
						'pv':description['PV'],
						'direction':int(description['Direction']),
						'frame':int(description['Frame']),
						'size':np.array([int(description['SizeX']),int(description['SizeY']),int(description['SizeZ'])]),
						'workDistance':np.array([int(description['WorkDistanceX']),int(description['WorkDistanceY']),int(description['WorkDistanceZ'])]),
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
							description['Name'],
							**(kwargs))
				# Set a ui for the motor if we are doing that.
				if self._ui is not None:
					newMotor.setUi(self._ui)
				# Append the motor to the list.
				self.motors.append(newMotor)
		# Set the order of the list from 0-i.
		self.motors = sorted(self.motors, key=lambda k: k._order) 
		# Update the stage details.
		self._name = stage
		# Calibrate with no calibration offset. This can be recalculated later.
		self.calibrate(np.array([0,0,0]))
		# Update GUI.
		if self._ui is not None:
			self._ui.update()

	def calibrate(self,calibration):
		# Stage size in mm including calibration offset (i.e. a pin or object used to calibrate the stage).
		self._offset = calibration
		self._size = calibration
		for motor in self.motors:
			if motor._stage == 0:
				self._size = np.add(self._size,motor._size)

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
			if (motor._stage == 1)&(motor._type == 0):
				# Read motor position and the axis it works on.
				mpos = motor.readPosition()
				axis = motor._axis
				# Add value to the overall position.
				if mpos == np.inf: mpos = 0
				pos[axis] += mpos

		# Return the position.
		if idx is not None:
			return pos[idx]
		else: 
			return pos

	def calculateMotion(self,G,variables):
		# We take in the 4x4 transformation matrix G, and a list of 6 parameters (3x translations, 3x rotations).
		self.i += 1
		if self.i > 10: return
		# Create a transform for this stage, S.
		print('Stage Name: ',self._name)
		print('Variables:',variables)
		S = np.identity(4)
		Si = np.identity(4)
		# Position of motor in stack (in mm).
		stackPos = np.array([0,0,0])
		# NICE PRINTING!!!!!!!!!NICE PRINTING!!!!!!!!!NICE PRINTING!!!!!!!!!NICE PRINTING!!!!!!!!!NICE PRINTING!!!!!!!!!
		np.set_printoptions(formatter={'float': lambda x: "{0:0.2f}".format(x)})
		# Make a copy so original stays intact.
		calcVars = np.array(variables)
		# Iterate over each motor in order.
		for motor in self.motors:
			print('Motor Name: ',motor._name)
			# Get the x y z translation or rotation value.
			value = calcVars[(motor._axis + (3*motor._type))]
			# Take as much of this as you can if it fits within the limits of the motor!!
			# print('calcVars before',calcVars)
			# Set the taken variable to 0. This stops any future motor from taking this value.
			calcVars[(motor._axis + (3*motor._type))] = 0
			# print('calcVars after',calcVars)
			# Add current motor height in stack.
			if motor._stage == 0:
				stackPos += motor._size
			# If it has a working distance, update the working point.
			if sum(motor._workDistance) > 0:
				# Get the current position of the stage.
				stagePos = self.position()
				motor.calculateWorkPoint(stagePos,self._size,stackPos)
			# Get the transform for the motor.
			if motor._type == 0:
				T = motor.transform(value)
				Ti = np.identity(4)
			elif motor._type == 1:
				T, Ti = motor.transform(value)
			# Multiply the transform into the overall transform.
			# print('****** MOTOR NUMBER ',motor._order,':')
			# print('====== T:')
			# print(T)
			S = S@T
			Si = Si@Ti 
			# print('=== S:')
			# print(S)
		# Take out all unecessary shit. (Undo maths for translations on rotations.)
		St = S@Si
		# Now we have S, a 4x4 transform that encompases all motors.
		print('****** RESULTS:')
		print('====== Global:')
		print(G)
		print('====== Stage:')
		print(St)
		remainder = np.linalg.inv(St)@G
		print('====== Remainder:')
		# remainder[:3,3] = G[:3,3]+S[:3,3]
		print(remainder)
		t = np.array(St[:3,3]).reshape(3,)
		r = np.array(St[:3,:3]).reshape(3,3)

		# Start by assuming a successful decomposition.
		success = True

		# Update variables to match stage movements.
		print('a:',np.sum(remainder[:3,3]))
		if np.isclose( np.sum(np.absolute(remainder[:3,3])) ,0, atol=1e-02) is False:
			# Check to see if remainder is within less than 1 micron tolerance.
			# If the translations aren't 0 then subtract the updates to the vars.
			# print('variables before additions: ',variables[:3])
			# print('remainder: ',remainder[:3,3])
			
			print('variables:',variables)
			print('stage pos:',S)
			# May have to rejig this for other stages where it goes through the actual process?
			# variables[:3] += S[:3,:3]@remainder[:3,3]
			variables[:3] = np.linalg.inv(S[:3,:3])@G[:3,3]
			print('variables changed:',variables)
			# variables[:3] += remainder[:3,3]@S[:3,:3]
			# variables[:3] -= remainder[:3,3]@S[:3,:3]

			# variables[:3] -= np.array(S[:3,3]@remainder[:3,3]).reshape(3,)
			# print('S: ',S[:3,3])
			# print('S: ',S[:3,3])
			# print('combined: ',S[:3,3] - remainder[:3,3])
			# variables[:3] = S[:3,3] - remainder[:3,3]
			# print('variables after additions: ',variables[:3])
			success = False

		# Extract any extra angles or just report back whats missing. This involves extracting angles.
		# Can do something with varTracking to see how many have gone down to 0. Can be used to show that we can't account for some parts of the movement?

		# Re-iterate this function with the adjusted vars.
		if success is False:
			self.calculateMotion(G,variables)

		elif success is True:
			# Exit the function.
			self._motion = variables
			print('Self Motion on success:',self._motion)
			return variables

	def applyMotion(self,variables=None):
		# If no motion is passed, then apply the preloaded motion.
		if variables == None:
			variables = self._motion
			print('inside apply motion, vars are now motion:',variables)
		# Iterate over each motor in order.
		for motor in self.motors:
			# Understand the motors function.
			index = motor._axis + (3*motor._type)
			# Get the x y z translation or rotation value.
			value = variables[index]
			# Apply the value.
			motor.shiftPosition(value)
			print('Moving ',motor._name,value)
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