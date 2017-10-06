import numpy as np

class detector:
	def __init__(self):
		self.detector = None
		self.pixelSize = np.array(0,0)
		self.imageSize = np.array(0,0)
		# ROI is lr-bt
		self.roi = np.array([0,0,0,0])

		self.pv = {}
		self.pv['acquire'] = None