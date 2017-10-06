'''
This class is designed to hold an image and it's parameters.
'''

class image:
	def __init__(self,array):
		# Pixel data.
		self.array = np.array(array)
		# Extent: Left, Right, Bottom, Top.
		self.extent = [-1,1,-1,1]
		# Image dimensions (1,2 or 3).
		self.dimensions = 2
		# Pixel size and shape.
		self.pixelSize = [1,1]
		self.pixelShape = 'Square'
		# Isocenter value of image (point of interest).
		self.isocenter = [0,0]

	def setExtent(self,extent):
		''' Write new extent. '''
		check = False
		# Check: must have 4 values for 2D, 6 values for 3D.
		if (len(extent)==4) & (len(np.shape)==2):
			# 2D image.
			self.dimensions = 2
			self.extent = extent