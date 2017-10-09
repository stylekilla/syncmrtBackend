'''
CLASS IMAGE
+ Houses information about array + metadata.
+ Metadata is:
-	filepath 		the filepath to the folder containing the dataset
-	dataset 		the dataset of file(s)
-	array 			a numpy 2D array of values
-	extent 			the extent of the image (LRBT)
-	pixel size 		pixel size of the image
-	position		position where the image was taken
-	isocenter 		location of isocenter of the 2D image
'''
class image:
	def __init__(self):
		# The local filepath to the image dataset.
		self.fp = None
		# The file dataset for the image(s).
		self.ds = None
		# Array data for image.
		self.array = None
		# Extent of image, BT-LR-FB.
		self.extent = None
		# Pixel size of image.
		self.pixelSize = None
		# Top left corner of image.
		self.position = None
		# Isocenter of the image.
		self.isocenter = None
		'''
		FOR RTPLANS
		'''
		# Mask Options
		self.mask = None
		self.maskThickness = None
		# Rotation options
		self.collimator = None
		self.gantry = None
		self.patientSupport = None
