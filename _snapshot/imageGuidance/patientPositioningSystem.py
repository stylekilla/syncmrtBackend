import numpy as np
from PyQt5 import QtCore
from syncmrt.tools.math.dependencies import *

class newSystem(QtCore.QObject):
	stageConnected = QtCore.pyqtSignal(bool)

	def __init__(self):
		'''
		RAGE AGAINST THE MACHINE!
		- This is a machine that has information about current patient position.
		- We are modelling just the MRT stage in Hutch 2B to begin with.
		- An inf value is code for 'no valid value or stage/motor.'
		'''
		super().__init__()

		# Patient Positioning Stage Name
		self.stage = None
		self.patientMotorOrder = None
		# Patient Positioning Motors
		self.tx = None
		self.ty = None
		self.tz = None
		self.rx = None
		self.ry = None
		self.rz = None

		# Detector
		self.detector = None

		# Bool states.
		self._isStageConnected = False
		self._isDetectorConnected = False

		# Center of rotations for x, y and z.
		self.rxcor = np.array([np.inf,np.inf,np.inf])
		self.rycor = np.array([np.inf,np.inf,np.inf])
		self.rzcor = np.array([np.inf,np.inf,np.inf])

		# Infinity should point to an undef position.
		self.patientIsoc = np.array([np.inf,np.inf,np.inf])
		# Beam isoc is nominally 0,0,0.
		self.beamIsoc = np.array([0,0,0])

	def setStageConnected(self,state):
		''' Set if the stage is connected or not. '''
		self._isStageConnected = bool(state)
		self.stageConnected.emit(self._isStageConnected)

	def isStageConnected(self):
		''' Must have all viable motors for this to be true. '''
		return self._isStageConnected

	def getMotorOrder(self):
		if self._isStageConnected:
			# If a stage is connected, extract the order.
			patientMotors = [self.tx,self.ty,self.tz,self.rx,self.ry,self.rz]
			# Maximum index of motors.
			index = 5
			# New dict for motor order (e.g. order[0]=txmotor)
			self.patientMotorOrder = {}
			# Scan through the motors and find their order.
			for motor in patientMotors:
				if motor:
					# If we have a valid motor (i.e. not None), continue.
					if motor._order:
						# If it has an order value, write it.
						self.patientMotorOrder[int(motor._order)] = motor
					else:
						# If it does not have a value, add it in reverse.
						self.patientMotorOrder[index] = motor
						# Dec index by 1.
						index -= 1
				else:
					# If not a valid motor (i.e. None), pass.
					pass

	def setDetectorConnected(self,state):
		self._isDetectorConnected = bool(state)
		return self._isDetectorConnected

	def connectStages(self,motorList):
		# Connect the stages.
		self.tx = motorList['tx']
		self.ty = motorList['ty']
		self.tz = motorList['tz']
		self.rx = motorList['rx']
		self.ry = motorList['ry']
		self.rz = motorList['rz']
		# Update motor order.
		self.getMotorOrder()

	def whereIsPatient(self):
		# If no stage is connected return 0.
		if not self._isStageConnected:
			return 0

		# Read values.
		if self.tx: tx = self.tx.read()
		else: tx = np.inf
		if self.ty: ty = self.ty.read()
		else: ty = np.inf
		if self.tz: tz = self.tz.read()
		else: tz = np.inf
		if self.rx: rx = self.rx.read()
		else: rx = np.inf
		if self.ry: ry = self.ry.read()
		else: ry = np.inf
		if self.rz: rz = self.rz.read()
		else: rz = np.inf

		return np.array([tx,ty,tz,rx,ry,rz])

	def movePatient(self,position,mode='relative'):
		'''
		The motor order for moving the patient should be as extracted by the solver.
		This is important for ROTATIONS as they are not commutative. For translations it does not matter.
		This order is x-y-z (as per the synchrotron cs).
		x+: downstream
		y+: left horizontal looking downstream
		z+: vertical
		'''
		# Is a stage connected?
		if not self._isStageConnected:
			# No (False)? return 0.
			return 0

		# Extract individual xyz translations and rotations for the movement.
		tx,ty,tz,rx,ry,rz = position
		position = {}
		position['tx'] = tx
		position['ty'] = ty
		position['tz'] = tz
		position['rx'] = rx
		position['ry'] = ry
		position['rz'] = rz

		# Starting patient position.
		start = self.whereIsPatient()

		'''
		# Recalculate H1 and H2.
		tx,ty = self.motorAssociation([tx,ty])

		# Write values.
		if self.tx: self.tx.write(tx,mode)
		if self.ty: self.ty.write(ty,mode)
		if self.tz: self.tz.write(tz,mode)
		if self.rx: self.rx.write(rx,mode)
		if self.ry: self.ry.write(ry,mode)
		if self.rz: self.rz.write(rz,mode)
		'''

		# Check motor application order
		if self.patientMotorOrder:
			print('In patient motor order:')

			# If there is a specified order, follow it.
			for i in range(len(self.patientMotorOrder)):
				# Get the motor to move.
				motor = self.patientMotorOrder[i]
				# Get the movement of that motor.
				movement = motor._movement
				# Get the value to write to the motor.
				value = position[movement]

				if motor._dependentOn:
					print('Motor has dependency: ',motor._dependentOn)
					# Are there any dependencies?
					if (motor._movement[0]=='t')&(motor._dependentOn[0]=='r'):
						# It is dependent on a rotation.
						value = translationOnRotation(value,motor._dependentOn,solveFor=motor._movement)
						print('Solving ',motor._movement,'dependent on ',motor._dependentOn,', recalculated ',position[movement],'to be ',value)
					elif (motor._movement[0]=='r')&(motor._dependentOn[0]=='t'):
						# It is dependent on a translation.
						# This is not yet implemented.
						pass
					else:
						# Do nothing.
						pass

				# Move the motor.
				self.patientMotorOrder[i].write(value,mode)

		else:
			# If no order is specified, write values in xyz order.
			print('Just exectuting write values in xyz order.')
			if self.tx: self.tx.write(tx,mode)
			if self.ty: self.ty.write(ty,mode)
			if self.tz: self.tz.write(tz,mode)
			if self.rx: self.rx.write(rx,mode)
			if self.ry: self.ry.write(ry,mode)
			if self.rz: self.rz.write(rz,mode)

		# Final patient position.
		end = self.whereIsPatient()

		# Different in patient position should equal the changes made.
		completion = (start-end)+np.array([tx,ty,tz,rx,ry,rz])

		return completion

	# # Could be:
	# # def motorAssociation(self,master,slaves):
	# def motorAssociation(self,translation):
	# 	# Check dependencies.
	# 	if (self.tx.dependentOn == 'rz')&(self.ty.dependentOn == 'rz')&(self.rz is not None):

	# 		# tx,ty = translation
	# 		rz = self.rz.read()
	# 		print('rz',rz)

	# 		if rz is np.inf:
	# 			print('No Rz motor connected, cannot retrieve current position.')
	# 			return 0,0
	# 		else:
	# 			# tx,ty = relativeTranslation(rz,[tx,ty])
	# 			tx,ty = translationOnRotation(translation,rz)

	# 		return tx,ty

	def connectMotors(self,motorList):
		# Connect the motors.
		self.tx = motorList['tx']
		self.ty = motorList['ty']
		self.tz = motorList['tz']
		self.rx = motorList['rx']
		self.ry = motorList['ry']
		self.rz = motorList['rz']










'''
		# A list of 6 motors (translation and rotation in xyz) available to use for patient alignment.
		# These motors must match the synchrotron coordinate system.
		self.motor = epicsStages

		# Access to user interface feedback mechanism. Usually a QtModel.
		self.gui = guiDisplay

		# Centre of Rotation
		self.cor = cor
		# Beam Isocentre
		self.isoc = isoc
		# Axes order (xyz = 012).
		self.axesOrder = {}
		self.axesOrder['x'] = 0
		self.axesOrder['y'] = 1
		self.axesOrder['z'] = 2
		# Axes mapping.
		self.axesMapping = {}
		self.axesMapping['x'] = 'x'
		self.axesMapping['y'] = 'z'
		self.axesMapping['z'] = 'y'

		# Options.
		self._corIsFixed = True
		self._txMovesWithRotation = False
		self._tyMovesWithRotation = False
		self._tzMovesWithRotation = False
		self._rxMovesWithTranslation = False
		self._ryMovesWithTranslation = False
		self._rzMovesWithTranslation = False

	def movePatient(self,translation,rotation):
		# First translate into beam isoc.
		self.translate(translation)

		# We are now in the correct position but wrong orientation.
		rx,ry,rz = rotation

		if self._corIsFixed:
			# Rotate point by amount around fixed cor.
			self.rotate(rotation)
			# Find translation required to bring it back into centre.
			from syncmrt.tools import math
			currentPos = self.whereIsPatient()[0:3]
			rotTranslation = -math.fixedRotation(currentPos,self.cor,rx,ry,rz)
			self.translate(rotTranslation)

		else:
			# Set center of rotation.

			# Apply rotations.
			self.rotate(rotation)

	def translate(self,translation):
		# Translate the patient.
		tx,ty,tz = translation

		if (self._txMovesWithRotation+self._tyMovesWithRotation)==2:
			# This means our translation stages are on top of our vertical rotation stage.
			currentPos = self.whereIsPatient()
			tx, ty = math.secondaryTranslation(rz,[tx,ty])

		# Apply the translations to the motors.
		self.move('tx',tx)
		self.move('ty',ty)
		self.move('tz',tz)

	def rotate(self,rotation):
		# Translate the patient.
		rx,ry,rz = rotation
		self.move('rx',rx)
		self.move('ry',ry)
		self.move('rz',rz)

	def move(self,motorid,amount):
'''
'''
		Ensure inputs are of correct types, converting float to 3 dec places (0.001 mm)
'''

		# motorid = str(motorid)
		# value = round(float(amount),3)

		# if self.motor[motorid] is not None:
		# 	self.motor[motorid].writeValue('VAL',value=value)
		# else:
		# 	print('No motor for',motorid,'to move',amount,'.')

		# '''Connect to motors and apply alignment'''
		# # Get the current position of the motor.
		# currentPos = self.controls.patient['tx'].readValue('RBV')
		# # The amount to change by (inclusive of direction).
		# changePos = self.alignmentSolution.translation[0]
		# # Calculate new value in reference current value.
		# newPos = currentPos + changePos
		# # Write new value to motor.
		# self.controls.patient['tx'].writeValue('VAL',value=newPos)
		# # Update sidepanel as we go.

		# self.property.updateVariable('Alignment',['Rotation','x','y','z'],[float(self.alignmentSolution.x),float(self.alignmentSolution.y),float(self.alignmentSolution.z)])
		# self.property.updateVariable('Alignment',['Translation','x','y','z'],self.alignmentSolution.translation.tolist())