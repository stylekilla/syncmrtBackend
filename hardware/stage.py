from syncmrt.hardware.motor import motor
from syncmrt.widgets import QEMotor

class stage:
	def __init__(self,motorList,ui=None):
		# Information
		self._name = None
		self._dof = (0,[0,0,0,0,0,0])
		self.motors = []
		# A preloadable motion.
		self._motion = None
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

	def load(self,name):
		# Remove all motors.
		for item in self.motors:
			del item
		# Iterate over new motors.
		for description in self.motorList:
			if description['Stage'] == name:
				wp = [0,0,0]
				if int(description['Axis']) < 3:
					wp[int(description['Axis'])] = int(description['WorkDistance'])
				else:
					wp[int(description['Axis'])-3] = int(description['WorkDistance'])
				# Define the new motor.
				newMotor = motor(int(description['Axis']),
							int(description['Type']),
							pv=description['PV'],
							direction=int(description['Direction']),
							workDistance=int(description['WorkDistance']),
							workPoint=wp)

				if self._ui is not None:
					newMotor.setUi(self._ui)
				# Append the motor to the list.
				self.motors.append(newMotor)
		# Update the name.
		self._name = name
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

	def position(self):
		# return the current position in Global XYZ.
		pass

	def calculateMotion(self,G,variables):
		# We take in the 4x4 transformation matrix G, and a list of 6 parameters (3x translations, 3x rotations).
		# Create a transform for this stage, M.
		S = np.identity(4)
		# Iterate over each motor in order.
		for idx, motor in self.motors:
			# Get the x y z translation or rotation value.
			value = variables[(motor._axis + (3*motor._type))]
			# Take as much of this as you can if it fits within the limits of the motor!!

			# Set the taken variable to 0. This stops any future motor from taking this value.
			variables[(motor._axis + (3*motor._type))] = 0
			# If it is a rotation, update the working point.
			if motor._type == 1:
				motor.calculateWorkPoint(M)
			# Get the transform for the motor.
			T = motor.transform(value)
			# Multiply the transform into the overall transform.
			S = S@T
		# Now we have S, a 4x4 transform that encompases all motors.
		Remainder = G@np.linalg.inv(S)

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