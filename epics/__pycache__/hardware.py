'''
class detector:
	__init__ requires a name (string) for the detector and base PV (string) to connect to.
	setup specifies some useful variables for the detector and it's images
'''
class detector:
	def __init__(self,name,pv,fp=None,ui=None):
		self._name = str(name)
		self._pv = str(pv)
		self._ui = None
		self._fp = 'Z:/syncmrt/images'

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

'''
class detector:
	__init__ requires a name (string) for the detector and base PV (string) to connect to.
	setup specifies some useful variables for the detector and it's images
'''
class stage:
	def __init__(self):
		# A 6D machine, defined by global xyz positions and orientations.
		self.motor = []
		# Isocenter of machine. Should be pre-calibrated.
		self._origin = [0,0,0]

	def setStage(self):
		# Set the current stage.
		pass

	def setPosition(self):
		# Absolute movement.
		pass

	def shiftPosition(self):
		# Relative movement.
		pass

	def position(self):
		# Return current position.
		pass

	def setIsocenter(self):
		pass

	def setOrigin(self):
		pass
