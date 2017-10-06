class stage:
	def __init__(self):
		self._dof = (0,[0,0,0,0,0,0])
		self.motors = {}

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
		# return the current position.
		pass

	def calculateMotion(self,variables):
		# Take in a tuple of length 6, this is x y z translations and rotations.
		# Create a transform for this stage, M.
		M = np.identity(4)
		# Iterate over each motor in order.
		for idx, motor in self.motors:
			# Get the x y z translation or rotation value.
			value = variables[(motor._axis + (3*motor._type))]
			# Set the taken variable to 0. This stops any future motor from taking this value.
			variables[(motor._axis + (3*motor._type))] = 0
			# If it is a rotation, update the working point.
			if motor._type == 1:
				motor.calculateWorkPoint(M)
			# Get the transform for the motor.
			T = motor.transform(value)
			# Multiply the transform into the overall transform.
			M = M@T
		# Now we have M, an identity matrix that encompases all motors.
		return M
		# Mt = np.array(M[:3,3]).reshape(3,)

		# We have an adjusted matrix, M, that accounts for fixed motor movements etc.
		# We must go through and divvy up the translations again, this time applying them.

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

# This is an epics based class? Qt?
class motor:
	def __init__(self):
		# Axis can be 0,1,2 to represent x,y,z.
		self._axis = None
		# Type is 0 (translation) or 1 (rotation).
		self._type = 0
		# Direction is +1 (forward) or -1 (reverse) for natural motor movement.
		self._direction = 1
		# Upper and lower limits of motor movement.
		self._range = [-np.inf,np.inf]
		# Define a work point for the motor, this will be non-zero if it has a fixed mechanical working point. This is nominally the isocenter of the machine.
		self._workDistance = 0
		self._workPoint = [0,0,0]
		# Interfaces.
		self._ui = None
		self._control = None

	def setUi(self):
		# Connect user interface.
		pass

	def setPv(self):
		# Set the base PV for the motor.
		pass

	def setPosition(self,position):
		pass

	def shiftPosition(self,position):
		pass

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

