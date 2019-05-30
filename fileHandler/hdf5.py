import h5py as h5
from datetime import datetime as dt
import logging

_xrayImageAttributes = [
		"Date",
		"Time",
		"datetime",
		"Comment",
		"PatientSupport",
		"PatientSupportAngle",
		"PatientSupportPosition",
		"Detector",
		"ImageSize",
		"PixelSize",
		"ROI",
		"AcquisitionTime",
		"AcquisitionPeriod",
		"WigglerField",
		"Filtration",
		"Mode",
		"BeamEnergy",
		"FieldSize",
		"M",
		"Mi",
	]

# Create a new HDF5 file.
def new(fp):
	f = file(fp,'w')
	# Set the file up.
	f.create_group('Patient')
	f.create_group('Image')
	# Return the file.
	return f

# Load a HDF5 file.
def load(fp):
	print(fp)
	return file(fp,'w')

class file(h5.File):
	def __init__(self,fp,mode,*args,**kwargs):
		super().__init__(fp,mode,*args,**kwargs)

	def getImages(self,index=-1):
		pass


# class base:
# 	file = None
# 	def __init__(self,patientName,fp,init=False):
# 		# Open file with write permissions.
# 		self.file = h5.File(fp,'w')
# 		self.file.create("PatientName",patientName)

# 	def new(self,file):
# 		self.open(file)

# 	def open(self,file):
# 		# Close if one is already open.
# 		if file is not None:
# 			self.close()
# 		# Connect to new file.
# 		self.file = h5.File(file,'w')

# 	def close(self):
# 		self.file.close()


# class xray(base):
# 	def __init__(self):
# 		super().__init__()

# 	def newSet(self):
# 		# Create a new group labeled as the next available index.
# 		index = len(self.file["Image"])
# 		container = self.file["Image"].create_group(str(index))
# 		# Return the reference to the image.
# 		return container

# 	def _finaliseSet(self,set):
# 		# Calculate no of image sets for the file.
# 		self.file.create("NumberOfImageSets",len(self.file['Image']))
# 		# Calculate no of images per set.
# 		self.file["Image"].create("NumberOfImages",len(set))
# 		# Machine iso?
# 		self.file["Image"].create("NumberOfImages",len(set))
# 		# Separation between images?
# 		if len(set) == 2:
# 			self.file["Image"].create("SeparationBetweenImages",len(set))
# 			self.file["Image"].create("MachineIsocenter",len(set))

# 	# def readSet(self,set):


# 	def newImage(self,set,array,**kwargs):
# 		# Create timestamp.
# 		time = dt.now()
# 		# Create a new image in a set.
# 		index = len(set)
# 		image = set.create_dataset(str(index),array,array.dtype)
# 		# Attributes: dataset.create(name, data, shape=None, dtype=None)
# 		# Date and time information.
# 		image.create("Date",time.strftime("%d/%m/%Y"))
# 		image.create("Time",time.strftime("%H:%M:%S"))
# 		image.create("datetime",time)
# 		# Add the rest of the kwargs as attributes (if they are in the accepted list).
# 		for key, value in kwargs:
# 			if key in _xrayImageAttributes:
# 				image.create(key,value)
# 			else:
# 				logging.critical(str(key)+" is not a valid keyword for x-ray image attributes.")

# 	def readImage(self,set):
# 		# Get the array data for the image set.
# 		if len(set) == 0:
# 			return []
# 		elif len(set) == 1:
# 			return set["0"]
# 		elif len(set) == 2:
# 			return [set["0"],set["1"]]
# 		else:
# 			logging.critical("Something has gone wrong. Image set has a length of "+str(len(set)))
# 			return -1




# 	# def saveImage(self):

# 		# # Other.
# 		# image.create("Comment",)
# 		# # Patient Position Properties
# 		# image.create("PatientSupport",)
# 		# image.create("PatientSupportAngle",)
# 		# image.create("PatientSupportPosition",)
# 		# # Image properties.
# 		# image.create("Detector",)
# 		# image.create("ImageSize",)
# 		# image.create("PixelSize",)
# 		# image.create("ROI",)
# 		# image.create("AcquisitionTime",)
# 		# image.create("AcquisitionPeriod",)
# 		# # Beam Properties
# 		# image.create("WigglerField",)
# 		# image.create("Filtration",)
# 		# image.create("Mode",) # Monochromatic or Polychromatic
# 		# image.create("BeamEnergy",) # If Monochromatic, specify beam energy.
# 		# image.create("FieldSize",)
# 		# # Transform in and out of image axes.
# 		# image.create("M",)
# 		# image.create("Mi",)