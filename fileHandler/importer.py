import os
import pydicom as dicom
import numpy as np
from synctools.fileHandler import image
from natsort import natsorted
from synctools.tools.opencl import gpu as gpuInterface
import h5py
import logging

class importFiles:
	def __init__(self,ds,modality,ctImage=None):
		# Modality: 'xray' or 'ct'.
		self.modality = modality
		# Link to the dataset (Could be many files, for example, ct slices).
		self.ds = ds
		self.fp = os.path.dirname(ds[0])
		# Patient Name...?
		self.patientName = 'Unknown'
		# Image array.
		# self.image = [None,None]
		self.image = []
		# Patient isocenter.
		self.patientIsoc = None
		# self.plot = None
		
		if modality == 'CT':
			self.ds = self.checkDicomModality(modality)
			self.importCT()
		elif modality == 'MR':
			pass
		elif modality == 'XR':
			if len(self.ds) == 1:
				self.importXR()
			else:
				logging.critical('Synctools:fileHandler.dataset.py: Expected one file, instead recieved %i files.',len(self.ds))
		elif modality == 'RTPLAN':
			self.ds = self.checkDicomModality(modality)
			self.importRTPLAN(ctImage)
		else:
			# raise invalidModality
			logging.critical('Synctools:fileHandler.dataset.py: Invalid modality: %s.',modality)
			pass

	def importXR(self):
		# Read in hdf5 image arrays.
		file = h5py.File(self.ds[0],'r')
		# Load the images in.
		for i in range(file.attrs['NumberOfImages']):
			self.image.append(image())
			self.image[i].array = file[str(i)][:]
			# Extract the extent information, should be available in image.
			self.image[i].extent = file[str(i)].attrs['extent']
			# Image isocenter (typically the beam isocenter).
			self.image[i].isocenter = file[str(i)].attrs['isocenter']
			# Import image view.
			# self.image[i].view = file[str(i)].attrs['view']
			self.image[i].view = {
					'title':'AP',
					'xLabel':'LR',
					'yLabel':'SI',
				}

	def checkDicomModality(self,modality):
		# Start with empty list of files.
		files = {}
		for i in range(len(self.ds)):
			# Read the file in.
			testFile = dicom.read_file(self.ds[i])
			if testFile.Modality == modality:
				# Save in dict where the key is the slice position.
				files[int(testFile.SliceLocation)] = self.ds[i]
			else:
				pass

		# Sort the files based on slice location.
		sortedFiles = []
		for key in sorted(files.keys()):
			sortedFiles.append(files[key])

		# Return the sorted file list.
		return sortedFiles

	# def reloadFiles(self,files):
	# 	# Reload the files without losing plot or patient information.
	# 	self.ds = ds
	# 	self.fp = os.path.dirname(ds[0])
	# 	self.importXR()

	def importCT(self):
		# We are reading in a CT DICOM file.
		ref = dicom.read_file(self.ds[0])
		self.patientName = ref.PatientName
		# Create an image list.
		self.image = [image()]
		# Get DICOM shape.
		# shape = np.array([int(ref.Rows), int(ref.Columns), len(self.ds)])
		shape = np.array([int(ref.Columns), int(ref.Rows), len(self.ds)])
		# Initialize image with array of zeros.
		self.image[0].array = np.zeros(shape, dtype=np.int32)
		# For each slice extract the pixel data and put in respective z slice in array. 
		for fn in self.ds:
			data = dicom.read_file(fn)
			self.image[0].array[:,:,shape[2]-self.ds.index(fn)-1] = data.pixel_array
			# self.image[0].array[:,:,shape[2]-self.ds.index(fn)-1] = np.flipud(data.pixel_array)
		# Patient setup variables.
		self.image[0].position = ref.ImagePositionPatient
		self.image[0].patientPosition = ref.PatientPosition
		# Rescale the Hounsfield Units.
		self.image[0].array = (self.image[0].array*ref.RescaleSlope) + ref.RescaleIntercept
		# Sometimes the spacing between slices tag doesn't exist, if it doesn't, create it.
		try:
			spacingBetweenSlices = ref.SpacingBetweenSlices
		except:
			start = ref.ImagePositionPatient[2]
			file = dicom.read_file(self.ds[-1])
			end = file.ImagePositionPatient[2]
			spacingBetweenSlices = abs(end-start)/(len(self.ds)-1)
		# Voxel shape determined by detector element sizes and CT slice thickness.
		# self.image[0].pixelSize = [-ref.PixelSpacing[1],ref.PixelSpacing[0], spacingBetweenSlices]
		self.image[0].pixelSize = [ref.PixelSpacing[0], -ref.PixelSpacing[1], spacingBetweenSlices]
		# Note the axes that we are working on, these will change as we work.
		# self.image[0].axes = np.array([0,1,2])

		# CT array extent NP(l,r,b,t,f,b) or as DICOM(-x,x,y,-y,-z,z)
		# l, -x
		x1 = ref.ImagePositionPatient[0]-0.5*self.image[0].pixelSize[0]
		# r, +x
		x2 = ref.ImagePositionPatient[0]-0.5*self.image[0].pixelSize[0] + (shape[1]+1)*self.image[0].pixelSize[0]
		# b, +y
		y1 = ref.ImagePositionPatient[1]+0.5*self.image[0].pixelSize[1] - (shape[0]+1)*self.image[0].pixelSize[1]
		# t, -y
		y2 = ref.ImagePositionPatient[1]+0.5*self.image[0].pixelSize[1]
		# f, -z
		z1 = ref.ImagePositionPatient[2]+0.5*self.image[0].pixelSize[2] - (shape[2]+1)*self.image[0].pixelSize[2]
		# b, +z
		z2 = ref.ImagePositionPatient[2]+0.5*self.image[0].pixelSize[2]
		self.extent = np.array([x1,x2,y1,y2,z1,z2])

		'''
		Here we orientate the CT data with two assumptions:
			1. The CT was taken in HFS.
			2. At the synchrotron the patient is in an upright position.
		'''

		# GPU drivers.
		gpu = gpuInterface()

		'''
		The GPU has the following protocol:
			- Rotation happens about (col,row,depth).
			- The kwargs have two rotations (active and passive), these are lists [] of strings where:
				- '190' means take the first axis, '1' and rotate '90' degrees about it.
				- '0-90' means take the first axis, '0' and rotate '-90' degrees about it.
			- We must rotate all the ct dicom variables as we rotate the data.
				- Extent
				- Pixel Size
				- Any Isocenters
		'''

		# if self.image[0].patientPosition == 'HFS':
		# 	'''
		# 	Head First Supine position.
		# 	Here we rotate the CT to orientate it in an upright position (assuming the patient is upright at the synchrotron).
		# 	'''
		# 	kwargs = (
		# 		['0-90'],
		# 		self.image[0].pixelSize,
		# 		self.extent,
		# 		None
		# 		)
		# elif self.image[0].patientPosition == 'FFS':
		# 	# This would be another scan position for the patient.
		# 	kwargs = (
		# 		['090'],
		# 		self.image[0].pixelSize,
		# 		self.extent,
		# 		None
		# 		)
		# elif self.image[0].patientPosition == 'HFP':
		# 	# This would be another scan position for the patient.
		# 	kwargs = (
		# 		['090','2180'],
		# 		self.image[0].pixelSize,
		# 		self.extent,
		# 		None
		# 		)
		# else:
		# 	kwargs = (
		# 		[],
		# 		self.image[0].pixelSize,
		# 		self.extent,
		# 		None
		# 		)

		# Override
		kwargs = (
			['090'],
			self.image[0].pixelSize,
			self.extent,
			None
			)

		# Run the gpu rotation.
		self.image[0].array = gpu.rotate(self.image[0].array,*kwargs)

		# Update rotated variables from gpu.
		# self.image[0].axes = gpu.axes
		self.image[0].pixelSize = gpu.pixelSize
		self.image[0].extent = gpu.extent
		# Set empty isocenter for ct loading, update when rtplan is loaded.
		self.isocenter = np.array([0,0,0])

		# Save and write fp and ds.
		np.save(self.fp+'/ct0.npy',self.image[0].array)
		self.image[0].ds = [self.fp+'/ct0.npy']
		self.image[0].fp = os.path.dirname(self.image[0].ds[0])

	def importRTPLAN(self,ctImage):
		# Firstly, read in DICOM rtplan file.
		ref = dicom.read_file(self.ds[0])
		# Set file path.
		self.fp = os.path.dirname(self.ds[0])
		# We are reading in a RTPLAN DICOM file.
		self.patientName = ref.PatientName
		# Construct an object array of the amount of beams to be delivered.
		self.image = np.empty(ref.FractionGroupSequence[0].NumberOfBeams,dtype=object)
		# CT isocenter.
		temp = np.array(ref.BeamSequence[0].ControlPointSequence[0].IsocenterPosition)
		# self.ctisocenter = np.array([temp[0],temp[2],temp[1]])
		self.ctisocenter = np.array([temp[0],temp[2],temp[1]])

		# Load the GPU interface.
		gpu = gpuInterface()

		# Extract confromal mask data.
		for i in range(len(self.image)):
			self.image[i] = image()
			# self.image[i].block = np.empty(ref.BeamSequence[i].NumberOfBlocks,dtype=object)
			self.image[i].mask = ref.BeamSequence[i].BlockSequence[0].BlockData
			self.image[i].maskThickness = ref.BeamSequence[i].BlockSequence[0].BlockThickness

			'''
			We must now read in the Patient Support, Gantry, and Collimator rotation angles.
			These are rotations about the following axes:
				- Patient Support: Rotation about DICOM y in the CW direction.
				- Gantry: Rotation about DICOM z in the CCW direction.
				- Collimator: Rotation about rotated DICOM y axis in the ??CCW?? direction, after gantry rotation.
			'''

			self.image[i].gantry = float(ref.BeamSequence[i].ControlPointSequence[0].GantryAngle)
			self.image[i].patientSupport = float(ref.BeamSequence[i].ControlPointSequence[0].PatientSupportAngle)
			self.image[i].collimator = float(ref.BeamSequence[i].ControlPointSequence[0].BeamLimitingDeviceAngle)

			# self.image[i].pitchAngle = float(ref.BeamSequence[i].ControlPointSequence[0].TableTopPitchAngle)
			# self.image[i].rollAngle = float(ref.BeamSequence[i].ControlPointSequence[0].TableTopRollAngle)

			# Target isocenter position in DICOM (x,y,z).
			self.image[i].isocenter = np.array(ref.BeamSequence[i].ControlPointSequence[0].IsocenterPosition)

			# We must adapt isocenter point to match already orientated CT.
			print('isoc original:',self.image[i].isocenter)
			temp = self.image[i].isocenter 
			# self.image[i].isocenter = np.array([temp[0],temp[2],temp[1]])
			# self.image[i].isocenter = np.array([temp[1],temp[0],temp[2]])
			self.image[i].isocenter = np.array([temp[0],temp[2],temp[1]])
			print('isoc orientated:',self.image[i].isocenter)
			'''
			Keep in mind we must first rotate by the same rotation of the CT. 
			Rotation order for axes are:
				- 0: Collumn (horizontal)
				- 1: Row (vertical)
				- 2: Depth (into screen)

			The active rotations are made up of, in order:
				- Gantry (DICOM axis 2) // rot-ct axis 1
				- Collimator (DICOM axis 1) // rot-ct axis 2

			The passive rotations are made up of, in order:
				- Patient Support (DICOM axis 1) // rot-ct axis 2

			Rotations:
				Patient Support		DICOM Y		PYTHON-CT Depth(2)
				Gantry				DICOM Z		PYTHON-CT Col(1)
				Collimator			DICOM Y2	PYTHON-CT Depth(2)

				1. Patient Support
				2. Gantry, Collimator
			'''

			# gantry = '1'+str(self.image[i].gantry)
			# col = '2'+str(self.image[i].collimator)
			# patsup = '2'+str(-self.image[i].patientSupport)

			# Block 5:
			block3 = '0-4.97' 
			block5 = '090'

			# spesh = '0'+str(-self.image[i].gantry)
			rotationSet1 = [block5]
			# rotationSet1 = [patsup]
			# rotationSet2 = [gantry,col]
			kwargs = (
				rotationSet1,
				ctImage.pixelSize,
				ctImage.extent,
				self.image[i].isocenter
				)

			# Run the gpu rotation.
			self.image[i].array = gpu.rotate(ctImage.array,*kwargs)
			# Get rotated vars back from the gpu.
			self.image[i].pixelSize = gpu.pixelSize
			self.image[i].isocenter = gpu.isocenter
			self.image[i].extent = gpu.extent


			# BLOCK 5 RTP Y IS IN WRONG DIRECTION... FIX PLEASE.