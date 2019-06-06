from synctools.hardware.detector import detector
from synctools.fileHandler import hdf5
from PyQt5 import QtCore
import numpy as np
import logging

class Imager(QtCore.QObject):
	imageAcquired = QtCore.pyqtSignal(int)
	newImageSet = QtCore.pyqtSignal(str,int)

	# This needs to be re-written to accept 6DoF movements and split it up into individual movements.

	def __init__(self,database,ui=None):
		super().__init__()
		# Information
		self.currentDetector = None
		# File.
		self.file = None
		# Image buffer for set.
		self.buffer = []
		self.metadata = []
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
		logging.info("Loading the {} detector.".format(name))
		if name in self.deviceList:
			self.currentDetector = detector(name,self.detectors[name])

	def reconnect(self):
		self.currentDetector.reconnect()

	def setImagingParameters(self,params):
		# As they appear on PV's.
		self.detector.setParameters(params)

	def acquire(self,index,metadata):
		if self.file is None:
			logging.warning("Cannot acquire x-rays when there is no HDF5 file.")
			return None
		# Get the image and update the metadata.
		_data = self.detector.acquire()
		metadata.update(_data[1])
		# Add the transformation matrix into the images frame of reference.
		# Imagers FOR is a RH-CS where +x propagates down the beamline.
		M = np.identity(3)
		t = np.deg2rad(float(metadata['Image Angle']))
		rz = np.array([[np.cos(t),-np.sin(t),0],[np.sin(t),np.cos(t),0],[0,0,1]])
		M = rz@M
		metadata.update({
				'M':M,
				'Mi':np.linalg.inv(M),
			})
		# Append the image and metada to to the buffer.
		self.buffer.append((_data[0],metadata))
		# Emit a signal saying we have acquired an image.
		self.imageAcquired.emit(index)

	def setPatientDataset(self,_file):
		self.file = _file

	def addImagesToDataset(self):
		if file != None:
			_name, _nims = self.file.addImageSet(self.buffer)
			self.newImageSet.emit(_name, _nims)
		else:
			logging.critical("Cannot save images to dataset, no HDF5 file loaded.")