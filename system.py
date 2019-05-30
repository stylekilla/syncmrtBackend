from synctools import hardware, imageGuidance
import logging
import numpy as np

'''
class system:
	__init__ .
	The system holds information about the detector and stage.
	It should also hold information about... other stuff.
'''
class system:
	def __init__(self,patientSupports,detectors):
		self.solver = imageGuidance.solver()
		# self.source = hardware.source()
		self.patientSupport = hardware.patientSupport(patientSupports)
		self.detector = hardware.detector(detectors)
		self._patient = None

	def loadPatient(self,patient):
		# Assumes patient has an already loaded x-ray dataset.
		self._patient = patient
		logging.info("System has been linked with the patient data.")

	def setStage(self,name):
		self.patientSupport.load(name)

	def setDetector(self,name):
		self.detector.load(name)

	def calculateAlignment(self):
		# Update variables.
		# self.solver.setVariable()
		# Solve for alignment solution.
		# self.solver.solve()
		# Decompose.
		self.patientSupport.calculateMotion(self.solver.transform,self.solver.solution)
		# Apply solution.
		# self.patientSupport.shiftPosition(stageSolution)

	def applyAlignment(self):
		# Tell the patientSupport to apply the calculated/prepared motion.
		self.patientSupport.applyMotion(None)

	def movePatient(self,amount):
		self.patientSupport.shiftPosition(amount)

	def acquireXray(self,theta,trans,comment=''):
		# Theta and trans are relative values.
		# How many xrays to acquire?
		n = len(theta)
		# Setup vars.
		tx = ty = rx = ry = 0
		# Get delta z.
		dz = np.absolute(trans[1]-trans[0])
		# Get the current patient position.
		preImagingPosition = self.patientSupport.position()
		# Signals and slots: Connections.
		self.patientSupport.finishedMove.connect()
		self.detector.imageAcquired.connect()
		# Take n images.
		for i in range(n):
			# Move to the imaging position.
			self.patientSupport.shiftPosition(tx,ty,trans[i],rx,ry,theta[i])
			# Now image.
			self._acquireXray(dz)
			# Do something with the image, comment, angle etc. Put it into HDF5 file.
			# Assume imaging sends back to pre-imaging pos. Repeat.
			# Calculate a relative change for the next imaging angle.
			try: 
				theta[i+1] = -(theta[i]-theta[i+1])
			except:
				pass
		# All x-rays are now acquired.
		# Signals and slots: Disconnect.
		self.patientSupport.finishedMove.disconnect()
		self.detector.imageAcquired.disconnect()

	def _acquireXray(self,deltaZ,mode='scan'):
		# Intital detector setup.
		kwargs = {':CAM:ImageMode':0,			# ImageMode = Single
			':CAM:ArrayCounter':0,				# ImageCounter = 0
			':TIFF:AutoSave':1,					# AutoSave = True
			':TIFF:FileName':'scan',			# FileName = 'scan1'
			':TIFF:AutoIncrement':1,			# AutoIncrement = True
			':TIFF:FileNumber':0				# NextFileNumber = 0
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