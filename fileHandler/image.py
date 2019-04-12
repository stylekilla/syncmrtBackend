__all__ = ['image2d']

class image2d:
	def __init__(self):
		# The local filepath to the image dataset.
		self.fp = None
		# The file dataset for the image(s).
		self.ds = None
		# Array data for image.
		self.pixelArray = None
		# Pixel size of image.
		self.pixelSize = None
		# Extent of image, BT-LR-FB.
		self.extent = None
		# Top left corner of image.
		# self.position = None
		# Patient isocenter within image, assumes single isoc.
		self.patientIsocenter = None
		# Orientation of the image.
		# self.orientation = [1,2,0]
		# Image view.
		self.view = {
			'title':'None',
			'xLabel':'None',
			'yLabel':'None',
		}

# class image3d:
# 	def __init__(self):
# 		super()
# 		self.orientation = None
# 		self.fp = None
# 		self.ds = None
# 		'''
# 		FOR RTPLANS
# 		'''
# 		# Mask Options
# 		self.mask = None
# 		self.maskThickness = None
# 		# Rotation options
# 		self.collimator = None
# 		self.gantry = None
# 		self.patientSupport = None
# 		# Support mutiple views of the image?
# 		self.views = None