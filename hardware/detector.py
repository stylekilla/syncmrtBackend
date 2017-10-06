'''
class detector:
	__init__ requires a name (string) for the detector and base PV (string) to connect to.
	setup specifies some useful variables for the detector and it's images
'''
class detector:
	def __init__(self,name=None,pv=None,fp=None,ui=None):
		self._name = str(name)
		self._ui = None
		self._epics = str(pv)
		self._fp = 'Z:/syncmrt/images'
		self.pixelSize = [1,1]
		self.imageSize = [0,0]
		self.imageIsocenter = [0,0]
		self.imagePixelSize = [1,1]

	def setup(self):
		self._acquire = PV(self._pv+':CAM:Acquire')
		# Region of interest.
		self._roix = PV(':CAM:SizeX_RBV')
		self._roiy = PV(':CAM:SizeY_RBV')
		self.roi = [self._roix,self._roiy]

	def setVariable(self,**kwargs):
		# Kwargs should be in the form of a dict: {'key'=value}.
		for key, value in kwargs:
			# Assumes correct value type for keyword argument.
			epics.caput(self._pv+str(key),value)

	def acquire(self):
		# Tell the detector to acquire an image.
		self._acquire.put(1)

	def saveHDF5(self):
		# Tell the detector to save an image.
		file = hdf.File(fn,"w")
		file.attrs['NumberOfImages'] = 2
		# Attributes
		file.attrs['Detector'] = self.name
		file.attrs['PixelSize'] = self.pixelSize
		file.attrs['ImageSize'] = self.imageSize
		file.attrs['ImageIsocenter'] = self.imageIsocenter
		file.attrs['ImagePixelSize'] = self.imagePixelSize
		# Image pixels.
		# Save
		file.close