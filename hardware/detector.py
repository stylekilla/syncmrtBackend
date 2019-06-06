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
		# self.imageSize = [0,0]
		self.imageIsocenter = [0,0]
		# self.imagePixelSize = [1,1]
		self._imageBuffer = []
		# Controllers.
		self._controller = controls.detector(pv)

	def reconnect(self):
		if self._controller is not None:
			self._controller.reconnect()

	# def setup(self):
	# 	self._acquire = PV(self._pv+':CAM:Acquire')
	# 	# Region of interest.
	# 	self._roix = PV(':CAM:SizeX_RBV')
	# 	self._roiy = PV(':CAM:SizeY_RBV')
	# 	self.roi = [self._roix,self._roiy]

	def setParameters(self,**kwargs):
		# Kwargs should be in the form of a dict: {'key'=value}.
		for key, value in kwargs:
			# Assumes correct value type for keyword argument.
			epics.caput(self._pv+str(key),value)

	def acquire(self):
		time = dt.now()
		metadata = {
			'Detector': self.name,
			'Pixel Size': self.pixelSize,
			'Image Isocenter': self.imageIsocenter,
			'Time': time.strftime("%H:%M:%S"),
			'Date': time.strftime("%d/%m/%Y"),
			'dateTime': time,
		}
		# Take a dark field?
		return (self._controller.readImage(), metadata)