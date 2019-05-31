from synctools.hardware.detector import motor
from synctools.fileHandler import hdf5
from PyQt5 import QtCore
import numpy as np
import logging

class Imager(QtCore.QObject):
	imageAcquired = QtCore.pyqtSignal()
	imagesWritten = QtCore.pyqtSignal()

	# This needs to be re-written to accept 6DoF movements and split it up into individual movements.

	def __init__(self,database,ui=None):
		super().__init__()
		# Information
		self.currentDevice = None
		# File.
		self.file = None
		self._buffer = []

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
			self._controller = controls.detector(self.detectors[name])

	def reconnect(self):
		self.currentDevice.reconnect()

	def setImagingParameters(self,params)
			# Acquire an image and add it to the buffer.
		settings = {
			'acquisitionTime': 0.500
		}

	def acquire(self,metadata):
		if self.file is None:
			logging.warniing("Cannot acquire x-rays when there is no HDF5 file.")
			return None

		self.buffer = self.detector.acquire()

	def commitBuffer(self):
		?

	def setDataset(self,fp):
		self.file = hdf5.load(fp)

	def addImagesToDataset(self):
		metadata = {
			'stuff': 3
		}
		self.file.addImages(self.buffer,metadata)