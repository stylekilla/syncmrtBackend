import numpy as np

class dataDicom:
	def __init__(self):
		'''Variables'''
		self.fp = None
		self.ds = None
		self.ref = None
		self.array3d = None
		self.pixelSize = None
		self.arrayNormal = None
		self.arrayNormalPixelSize = None
		self.arrayOrthogonal = None
		self.arrayOrthogonalPixelSize = None
		self.rescaleIntercept = None
		self.rescaleSlope = None
		self.patientOrientation = None
		self.patientIsoc = None
		self.userOrigin = None
		'''Classes'''
		self.plotEnvironment = None
		self.tableModel = None

class patient:
	def __init__(self):
		self.MarkerSize

class dataXray:
	def __init__(self):
		'''Variables'''
		self.fp = None
		self.ds = None
		self.arrayNormal = None
		self.arrayNormalPixelSize = None
		self.arrayOrthogonal = None
		self.arrayOrthogonalPixelSize = None
		self.patientOrientation = None
		self.patientIsoc = None
		self.alignmentIsoc = None
		'''Classes'''
		self.plotEnvironment = None
		self.tableModel = None


class dataRtp:
	'''Data organisation class'''
	def __init__(self):
		self.fp = None
		self.ds = None
		self.beam = False
		'''Classes'''
		self.plotEnvironment = None
		self.tableModel = None

class dataBeam:
	'''Treatment plan beam data (inside beam sequence)'''
	def __init__(self):
		self.numberOfBlocks = None
		self.blockData = None
		self.blockThickness = None
		self.gantryAngle = None
		self.pitchAngle = None
		self.rollAngle = None
		self.arrayNormal = None
		self.arrayNormalPixelSize = None
		self.arrayOrthogonal = None
		self.arrayOrthogonalPixelSize = None

# class dataXR:
# 	def __init__(self):
# 		self.fp = None				# X-Ray Filepath (string)
# 		self.ds = None				# X-Ray Dataset (list)
# 		self.ref = None				# Reference Dataset (string)
# 		self.PixelSize = np.zeros((1,3))	# Pixel references for 2D image...
# 		self.ImageDimensions = None			# Image dimensions
# 		self.Markers = None					# Marker list
# 		self.MarkersOptimised = None		# Optimised marker list
# 		self.MarkersSize = None				# Fiducial marker size
# 		self.im0 = None						# Image 1
# 		self.im90 = None					# Image 2
# 		self.PatientOrientation = None		# Image orientation
# 		self.PatientIsoc = np.array([107.9032,107.9032,79.3548])   	# Isocentre (y,x,z) in mm
# 		self.alignmentIsoc = np.array([107.9032,107.9032,79.3548])	# Isoc Goal (y,x,z) in mm

# class dataCT:
# 	def __init__(self):
# 		self.fp = None					# Filepath
# 		self.dsDicom = None				# Dicom Dataset
# 		self.dsImages = None			# Image Dataset
# 		self.ref = None					# Reference Dicom File
# 		self.radiograph = None			# CLASS for generating radiographs
# 		self.PixelSize = np.zeros((1,3))	# Pixel sizes (x,y,z)
# 		self.ImageDimensions = None			# Array size
# 		self.im0 = None					# Image at 0 degrees
# 		self.im90 = None				# Image at 90 degrees
# 		self.pix0 = None
# 		self.pix90 = None
# 		self.Markers = None				# Marker locations
# 		self.MarkersOptimised = None	# Optimised marker list
# 		self.MarkersSize = None			# Fiducial marker size
# 		self.PatientOrientation = None	# Orientation of image
# 		self.PatientIsoc = np.array([0,0,0])			# Isoc of dicom image
# 		self.UserOrigin = np.zeros((1,3))			# User origin of dicom image




'''
RTPLAN
Dose Reference Sequence = Number of beam doses to be delivered
Fraction Group Sequence = Number of fractions to be delivered
Beam Sequence = Number of beams to be delivered (should match dose reference sequence)
	Beam Number
		Block thickness
		Block Number of Points 
		Block Sequence = Beam Shape (conformal mask)
		A bunch of other stuff... not sure if useful.
	Control Point Sequence
		Beam Energy
		Dose Rate Set
		Gantry Angle
		Gantry Rotation Direction?
		Patient Support Angle
		Table Top Angles
		Table Top Vertical Position
		Table Top Lateral Position
		Table Top Longitudinal Position
		Isoc Position
		Table Top Pitch Angle
		Table Top Roll Angle
		Dose Reference Sequence (See first level)
Patient Setup Sequence
	Patient Position = HFS?
	Patient Setup Number 
	Setup Technique??
Approval Status
'''