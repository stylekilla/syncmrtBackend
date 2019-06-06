from synctools import hardware, imageGuidance
import logging
import numpy as np
from functools import partial
from PyQt5 import QtCore

"""
system.py
---------
This module creates a treatment 'system' that is made up of imaging devices, positioning aparatus, beam delivery controls etc.
"""
class system(QtCore.QObject):
	imagesAcquired = QtCore.pyqtSignal(int)
	newImageSet = QtCore.pyqtSignal(str)

	def __init__(self,patientSupports,detectors):
		super().__init__()
		self.solver = imageGuidance.solver()
		# self.source = hardware.source()
		self.patientSupport = hardware.patientSupport(patientSupports)
		self.imager = hardware.Imager(detectors)
		self.patient = None
		# Counter
		self._routine = None
		# When a new image set is acquired, tell the GUI.
		self.imager.newImageSet.connect(self.newImageSet)

	def loadPatient(self,patient):
		# Assumes patient has an already loaded x-ray dataset.
		self.patient = patient
		logging.info("System has been linked with the patient data.")

	def setLocalXrayFile(self,file):
		self.patient.load(file,'DX')
		# Link the patient datafile to the imager.
		self.imager.file = self.patient.dx.file

	def setStage(self,name):
		self.patientSupport.load(name)

	def setDetector(self,name):
		self.imager.load(name)

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
		# Start a new routine.
		self._routine = ImagingRoutine()
		# Theta and trans are relative values.
		# How many xrays to acquire?
		self._routine.counter = 0
		self._routine.counterLimit = len(theta)
		logging.info('Acquiring {} images at {}.'.format(len(theta),theta))
		# Get delta z.
		self._routine.tz = trans
		self._routine.dz = np.absolute(trans[1]-trans[0])
		logging.info("Calculated delta z as {}".format(self._routine.dz))
		# Get the current patient position.
		self._routine.preImagingPosition = self.patientSupport.position()
		logging.info("Current position at: {}".format(self._routine.preImagingPosition))
		# Signals and slots: Connections.
		# self.patientSupport.finishedMove.connect(partial(self._acquireXray,dz))
		# self.detector.imageAcquired.connect()
		self._startScan()

		# 	# Calculate a relative change for the next imaging angle.
		# 	try: 
		# 		theta[i+1] = -(theta[i]-theta[i+1])
		# 	except:
		# 		pass

	def _startScan(self):
		# Setup vars.
		tx = ty = rx = ry = 0
		# Move to first position.
		self.patientSupport.shiftPosition([tx,ty,self._routine.tz[0],rx,ry,self._routine.theta[0]])
		self.patientSupport.finishedMove.connect(partial(self._continueScan,'imaging'))
		self.imager.imageAcquired.connect(partial(self._continueScan,'moving'))

	def _continueScan(self,mode):
		# So far this will acquire 1 image per angle. It will not do step and shoot or scanning yet.
		if mode == 'imaging':
			# Finished a move, acquire an x-ray.
			self._routine.counter += 1
			tx,ty,tz,rx,ry,rz = self.patientSupport.position()
			metadata = {
				'Image Angle': self._routine.theta[self._routine.counter],
				'Patient Support Position': (tx,ty,tz),
				'Patient Support Angle': (rx,ry,rz),
				'Image Index': self._routine.counter,
			}
			self.imager.acquire(self._routine.counter,metadata)
		elif mode == 'moving':
			if self._routine.counter < self._routine.counterLimit:
				# Defaults for now.
				tx = ty = rx = ry = 0
				# Finished a move, acquire an x-ray.
				self.patientSupport.shiftPosition([tx,ty,self._routine.tz[self._routine.counter],rx,ry,self._routine.theta[self._routine.counter]])
			else:
				self._endScan()

	def _endScan(self):
		# Disconnect signals.
		self.patientSupport.finishedMove.disconnect()
		self.imager.imageAcquired.disconnect()
		# Finalise image set.
		self.imager.addImagesToDataset()
		# Put patient back where they were.
		self.patientSupport.finishedMove.connect(self._finishedScan)
		self.patientSupport.setPosition(self._routine.preImagingPosition)

	def _finishedScan(self):
		# Disconnect signals.
		self.patientSupport.finishedMove.disconnect()
		# Send a signal saying how many images were acquired.
		self.imagesAcquired.emit(self._routine.counterLimit)
		# Reset routine.
		self._routine = None

	def _acquireXray(self,deltaZ,mode='scan'):
		pass
	# 	# Intital detector setup.
	# 	kwargs = {':CAM:ImageMode':0,			# ImageMode = Single
	# 		':CAM:ArrayCounter':0,				# ImageCounter = 0
	# 		':TIFF:AutoSave':1,					# AutoSave = True
	# 		':TIFF:FileName':'scan',			# FileName = 'scan1'
	# 		':TIFF:AutoIncrement':1,			# AutoIncrement = True
	# 		':TIFF:FileNumber':0				# NextFileNumber = 0
	# 		}
	# 	# epics.caput(dtr_pv+':TIFF:FileTemplate','%s%s_%02d.tif')		# Filename Format
	# 	self.detector.setVariable(**kwargs)

	# 	# Record intial position to put everything back to after we finish.
	# 	_intialPosition = self.stage.position()

	# 	if mode == 'scan':
	# 		# Move to lower Z limit via translation.
	# 		self.stage.setPosition(object_bottom,axis=2)
	# 		# Get z position after move.
	# 		object_pos = self.stage.position()[2]

	# 		# Take an image.
	# 		self.detector.acquire()

	# 		# Delta H, the amount to move in the vertical direction for each step.
	# 		d_h = self.detector.roi[1]*0.95

	# 		while object_pos < object_top:
	# 			# Move 90% of the region of interest down.
	# 			self.stage.shiftPosition(-d_h,axis=2)
	# 			# Acquire and image.
	# 			self.detector.acquire()
	# 			# Update z position.
	# 			object_pos = self.stage.position()[2]
	# 			# Repeat until we have reached our object_top point.

	# 		# Once finished, move the object back to the start.
	# 		self.stage.setPosition(_initialPosition)

	# 	else:
	# 		self.detector.acquire()

		# Now reconstruct the image!
		# With name, name.

class ImagingRoutine:
	theta = []
	tz = [0,0]
	dz = 0
	preImagingPosition = None
	counter = 0
	counterLimit = 0