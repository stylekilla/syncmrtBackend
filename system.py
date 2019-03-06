from syncmrtBackend import hardware, imageGuidance

'''
class system:
	__init__ .
	The system holds information about the detector and stage.
	It should also hold information about... other stuff.
'''
class system:
	def __init__(self,stageList):
		self.solver = imageGuidance.solver()
		self.detector = hardware.detector()
		self.stage = hardware.stage(stageList)

		# Make a list of the stages.
		self.stageList = set()
		for motor in self.stage.motorList:
			self.stageList.add(motor['Stage'])

	def setStage(self,name):
		if name in self.stageList: 
			self.stage.load(name)

	def setDetector(self,name):
		pass

	def calculateAlignment(self):
		# Update variables.
		# self.solver.setVariable()
		# Solve for alignment solution.
		# self.solver.solve()
		# Decompose.
		self.stage.calculateMotion(self.solver.transform,self.solver.solution)
		# Apply solution.
		# self.stage.shiftPosition(stageSolution)

	def applyAlignment(self):
		# Tell the stage to apply the calculated/prepared motion.
		self.stage.applyMotion(None)

	def movePatient(self,amount):
		self.stage.shiftPosition(amount)

	def acquireXraySet(self):
		''' Routine for taking orthogonal x-rays via step-and-shoot. '''
		# Take first x-ray.
		self.acquireXray('xray0')
		# Rotate 90 degrees.
		self.stage.shiftPosition(90,axis=6)
		# Take second x-ray.
		self.acquireXray('xray90')
		# Rotate back to original position.
		self.stage.shiftPosition(-90,axis=6)

	def acquireXray(self,mode='scan',name='xray'):
		# Intital detector setup.
		kwargs = {':CAM:ImageMode':0,			# ImageMode = Single
			':CAM:ArrayCounter':0,						# ImageCounter = 0
			':TIFF:AutoSave':1,							# AutoSave = True
			':TIFF:FileName':'scan',						# FileName = 'scan1'
			':TIFF:AutoIncrement':1,						# AutoIncrement = True
			':TIFF:FileNumber':0						# NextFileNumber = 0
			}
		# epics.caput(dtr_pv+':TIFF:FileTemplate','%s%s_%02d.tif')		# Filename Format
		self.detector.setVariable(**kwargs)

		# Record intial position to put everything back to after we finish.
		_intialPosition = self.stage.position()

		if mode == 'scan':
			# Move to lower Z limit via translation.
			self.stage.setPosition(object_bottom,axis=2)
			# Get z position after move.
			object_pos = self.stage.position()[2]

			# Take an image.
			self.detector.acquire()

			# Delta H, the amount to move in the vertical direction for each step.
			d_h = self.detector.roi[1]*0.95

			while object_pos < object_top:
				# Move 90% of the region of interest down.
				self.stage.shiftPosition(-d_h,axis=2)
				# Acquire and image.
				self.detector.acquire()
				# Update z position.
				object_pos = self.stage.position()[2]
				# Repeat until we have reached our object_top point.

			# Once finished, move the object back to the start.
			self.stage.setPosition(_initialPosition)

		else:
			self.detector.acquire()

		# Now reconstruct the image!
		# With name, name.