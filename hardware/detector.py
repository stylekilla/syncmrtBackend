import epics
from synctools.epics import controls
from PyQt5 import QtCore
import logging
import numpy as np
from datetime import datetime as dt

'''
class detector:
	__init__ requires a name (string) for the detector and base PV (string) to connect to.
	setup specifies some useful variables for the detector and it's images
'''
class detector(QtCore.QObject):
	imageAcquired = QtCore.pyqtSignal()

	def __init__(self,name,pv):
		super().__init__()
		# self._name = str(name)
		self.name = name
		self.pv = pv
		self.pixelSize = [1,1]
		# Isocenter as a pixel location in the image.
		self.imageIsocenter = [0,0]
		# Make a buffer.
		self.buffer = []
		# Controllers.
		self._controller = controls.detector(pv)
		# Setup.
		self.setup()

	def reconnect(self):
		if self._controller is not None:
			self._controller.reconnect()

	def setup(self):
		if self._controller._connected:
			epics.caput(self.pv+':CAM:ImageMode','Single')
			epics.caput(self.pv+':CAM:AcquireTime',.055)
			epics.caput(self.pv+':CAM:AcquirePeriod',.055)
			epics.caput(self.pv+':TIFF:AutoSave','No')
		# Region of interest.
		# self._roix = PV(':CAM:SizeX_RBV')
		# self._roiy = PV(':CAM:SizeY_RBV')
		# self.roi = [self._roix,self._roiy]

	def setParameters(self,**kwargs):
		# Kwargs should be in the form of a dict: {'key'=value}.
		for key, value in kwargs:
			# Assumes correct value type for keyword argument.
			epics.caput(self._pv+str(key),value)

	def acquire(self,continous=False):
		time = dt.now()
		# HDF5 does not support python datetime objects.
		metadata = {
			'Detector': self.name,
			'Pixel Size': self.pixelSize,
			'Image Isocenter': self.imageIsocenter,
			'Time': time.strftime("%H:%M:%S"),
			'Date': time.strftime("%d/%m/%Y"),
		}
		# Take a dark field?
		if continous:
			# Assumes stage moving at constant speed.
			# Write all to buffer, then when finished return the image and metadata.
			return (self.buffer,metadata)
			# pass

		else:
			# Return a tuple of the image and metadata.
			logging.critical("Turning images upside down in controller cos ruby sucks.")
			return (self._controller.readImage(), metadata)

	def acquireContinous(self,array):
		self.buffer.append(array)