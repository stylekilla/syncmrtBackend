from synctools.hardware.detector import detector
from synctools.fileHandler import hdf5
from PyQt5 import QtCore
import numpy as np
import logging

class Imager(QtCore.QObject):
	"""
	A QObject class containing information about imager hardware (detector + source).

	Parameters
	----------
	database : str
		A link to a *.csv file containing information about the hardware.
	config : str
		Pass the configuration file section relating to the imager.
	ui : QtWidget
		Unused. Should allow for imager controls to be set up and placed within the gui by using the ui to set a layout and imager child widgets.

	Attributes
	----------
	imageAcquired : pyqtSignal(int)
		An image has been acquired by the imager.
	newImageSet : pyqtSignal(str, int)
		An image set has been acquired by the imager with set `name` and `n` images.
	detector : object
		A synctools.hardware.detector object.
	file : object
		A synctools.fileHandler.hdf5.file object. Patient HDF5 file for storing x-ray images in.
	buffer : list
		A buffer for image frames, these later get released as a image set (1 or 2 images).
	sid : float
		Source to Imager Distance in mm.
	sad : float 
		Source to Axis Distance in mm.
	detectors : dict
		Dictionary of available detectors in the system and their Epics PV's.
	deviceList : set
		A list of all the detector names available to the system.
	"""

	imageAcquired = QtCore.pyqtSignal(int)
	newImageSet = QtCore.pyqtSignal(str,int)

	def __init__(self,database,config,ui=None):
		super().__init__()
		# Information
		self.detector = None
		# File.
		self.file = None
		self.config = config
		# Image buffer for set.
		self.buffer = []
		self._stitchBuffer = []
		self.metadata = []
		# System properties.
		self.sid = self.config.sid
		self.sad = self.config.sad
		# Get list of motors.
		import csv, os
		# Open CSV file
		f = open(database)
		r = csv.DictReader(f)
		# Devices is the total list of all devices in the database.
		self.detectors = {}
		self.deviceList = set()
		for row in r:
			self.detectors[row['Detector']] = row['PV Root']
			self.deviceList.add(row['Detector'])

	def load(self,name):
		"""
		Load a detector into the imager configuration.

		Attributes
		----------
		name : str
			The name of the detector to look up in the database file.
		"""
		logging.info("Loading the {} detector.".format(name))
		if name in self.deviceList:
			self.detector = detector(name,self.detectors[name])
			self.detector.imageIsocenter = self.config.isocenter
			self.detector.pixelSize = self.config.pixelSize

	def reconnect(self):
		""" Reconnect the detector controller to Epics. Use this if the connection dropped out. """
		self.detector.reconnect()

	def setImagingParameters(self,params):
		""" As they appear on PV's. """
		self.detector.setParameters(params)

	def acquire(self,index,metadata,continuous=False):
		"""
		Grabs a single image frame and loads it into the buffer. 

		Parameters
		----------
		index : int
			The `index` of the image (1 or 2).
		metadata : dict
			A dictionary of arguments that should be written into the HDF5 file as image attributes.
		continuous : bool
			Continuous scan, set to False by default.
		
		Returns
		-------
		imageAcquired(i) : pyqtSignal
			Emits a signal saying that the image index `i` has been added to the image buffer with `(array, metadata)`.
		"""
		if self.file is None:
			logging.warning("Cannot acquire x-rays when there is no HDF5 file.")
			return None
		# Get the image and update the metadata.
		_data = self.detector.acquire(continuous)
		metadata.update(_data[1])
		# Calculate the extent.
		l = self.detector.imageIsocenter[0]*self.detector.pixelSize[0]
		r = l - _data[0].shape[0]*self.detector.pixelSize[0]
		t = self.detector.imageIsocenter[1]*self.detector.pixelSize[1]
		b = t - _data[0].shape[1]*self.detector.pixelSize[1]
		extent = (l,r,b,t)
		# Add the transformation matrix into the images frame of reference.
		# Imagers FOR is a RH-CS where +x propagates down the beamline.
		M = np.identity(3)
		t = np.deg2rad(float(metadata['Image Angle']))
		rz = np.array([[np.cos(t),-np.sin(t),0],[np.sin(t),np.cos(t),0],[0,0,1]])
		M = rz@M
		metadata.update({
				'Extent': extent,
				'M':M,
				'Mi':np.linalg.inv(M),
			})
		# Append the image and metada to to the buffer.
		self.buffer.append((_data[0],metadata))
		# Emit a signal saying we have acquired an image.
		self.imageAcquired.emit(index)

	def acquireStep(self,beamHeight):
		"""
		Grabs a small vertical section of a larger image. 

		Parameters
		----------
		beamHeight : float
			The vertical height of the beam used for imaging. This will specify the region of the image to acquire.

		Returns
		-------
		imageAcquired(-1) : pyqtSignal
			Emits signal with -1 to state part of an image has been acquired.
		"""
		if self.file is None:
			logging.warning("Cannot acquire x-rays when there is no HDF5 file.")
			return None
		# Define the region of interest.
		t = int(self.detector.imageIsocenter[1] - (beamHeight/self.detector.pixelSize[1])/2)
		b = int(self.detector.imageIsocenter[1] + (beamHeight/self.detector.pixelSize[1])/2)
		logging.critical("Top and bottom indexes of array are: {}t {}b.".format(t,b))
		# Get the image ROI and add it to the stitch buffer.
		self._stitchBuffer.append(list(self.detector.acquire()))
		self._stitchBuffer[-1][0] = self._stitchBuffer[-1][0][t:b,:]
		# Emit a signal saying we have acquired an image.
		logging.info("Step image acquired.")
		self.imageAcquired.emit(-1)

	def prepareScan(self,beamHeight,speed):
		"""
		Sets up a continuous scan over `time`.

		Parameters
		----------
		time : float
			The time 

		"""		
		if self.file is None:
			logging.warning("Cannot acquire x-rays when there is no HDF5 file.")
			return
		# Set detector acusition time. ROI? How to port images straight to me?
		kwargs = {
			':CAM:AcquireTime': beamHeight/speed,
			':CAM:AcquirePeriod': 0,
			':CAM:ImageMode': 'Continuous',
		}
		self.detector.setParameters(kwargs)


	def stitch(self,index,metadata,z,tz):
		"""
		The `imager._stitchBuffer` is stitched together and the complete image is sent to the `imager.buffer` along with its finalised metadata.
		Stitching assumes the middle of the beam window is the middle of the beam. No offset.

		Parameters
		----------
		index : int
			Index of the image to be stitched.
		metadata : dict
			The metadata of the image to be included in the HDF5 file as image attributes.
		z : float
			The `z` (vertical) position of the patient before imaging.
		tz : list
			The range of vertical movement as `[-tz,+tz]` relative to the pre-imaging position `z`.
		"""
		# Metadata
		finish = self._stitchBuffer[-1][1]
		metadata.update(finish)

		logging.critical("Stitching is out of order... why?")
		# Image.
		# image = self._stitchBuffer[0][0]
		# for i in (range(1,len(self._stitchBuffer))):
		# 	print("Stitching {} of {}".format(i,len(self._stitchBuffer)-1))
		# 	roi = self._stitchBuffer[i][0]
		# 	# Stack the image.
		# 	image = np.vstack((image,roi))

		# Stack the image.
		image = self._stitchBuffer[-1][0]
		for i in range(len(self._stitchBuffer)-1):
			image = np.vstack((image,self._stitchBuffer[i][0]))

		# Calculate the extent.
		logging.critical("Extent calculation for stitching is currently wrong. Unfinished")
		l = (image.shape[1]/2)*self.detector.pixelSize[1]
		r = -(image.shape[1]/2)*self.detector.pixelSize[1]
		t = z + tz[1] + 0.5*self._stitchBuffer[0][0].shape[0]*self.detector.pixelSize[0]
		b = z + tz[0] - 0.5*self._stitchBuffer[0][0].shape[0]*self.detector.pixelSize[0]
		extent = (l,r,b,t)
		logging.critical("Image array shape: {}.".format(image.shape))
		# Add the transformation matrix into the images frame of reference.
		# Imagers FOR is a RH-CS where +x propagates down the beamline.
		M = np.identity(3)
		t = np.deg2rad(float(metadata['Image Angle']))
		rz = np.array([[np.cos(t),-np.sin(t),0],[np.sin(t),np.cos(t),0],[0,0,1]])
		M = rz@M
		metadata.update({
				'Extent': extent,
				'M':M,
				'Mi':np.linalg.inv(M),
			})
		# Append the image and metada to to the buffer.
		self.buffer.append((image,metadata))
		# Clear the stitch buffer.
		self._stitchBuffer = []
		logging.info("Image stitched.")
		# Emit the signal
		self.imageAcquired.emit(index)

	def setPatientDataset(self,_file):
		self.file = _file

	def addImagesToDataset(self):
		if self.file != None:
			_name, _nims = self.file.addImageSet(self.buffer)
			logging.debug("Adding {} images to set {}.".format(_nims,_name))
			self.newImageSet.emit(_name, _nims)
		else:
			logging.critical("Cannot save images to dataset, no HDF5 file loaded.")
		# Clear the buffer.
		self.buffer = []