import os
import dicom
import numpy as np
from syncmrt.fileHandler import image
from natsort import natsorted
from syncmrt.tools.opencl import gpu as gpuInterface
import h5py

class dataset:
	def __init__(self,ds,modality):
		self.modality = modality
		self.ds = ds
		self.fp = os.path.dirname(ds[0])
		self.patientName = 'Unknown'

		self.image = [None,None]
		self.patientIso = None
		self.plot = None
		
		if modality == 'CT':
			self.ds = self.checkModality(modality)
			self.importCT()
		elif modality == 'MR':
			pass
		elif modality == 'XR':
			self.importXR()
		elif modality == 'RTPLAN':
			self.ds = self.checkModality(modality)
			self.importRTPLAN()
		else:
			# raise invalidModality
			pass


	def checkModality(self,modality):
		files = []
		for i in range(len(self.ds)):
			testFile = dicom.read_file(self.ds[i])
			if testFile.Modality == modality:
				files.append(self.ds[i])
			else:
				pass

		return natsorted(files)

	def reloadFiles(self,files):
		# Reload the files without losing plot or patient information.
		self.ds = ds
		self.fp = os.path.dirname(ds[0])
		self.importXR()

	def importCT(self):
		# We are reading in a CT DICOM file.
		ref = dicom.read_file(self.ds[0])
		self.patientName = ref.PatientName
		# Create an image list.
		self.image = [image()]
		# Get DICOM shape.
		shape = np.array([int(ref.Rows), int(ref.Columns), len(self.ds)])
		# Initialize image with array of zeros.
		self.image[0].array = np.zeros(shape, dtype=np.result_type(ref.pixel_array))-1000
		# For each slice extract the pixel data and put in respective z slice in array. 
		for fn in self.ds:
			data = dicom.read_file(fn)
			self.image[0].array[:,:,shape[2]-self.ds.index(fn)-1] = data.pixel_array
		# Patient setup variables.
		self.image[0].position = ref.ImagePositionPatient
		self.image[0].patientPosition = ref.PatientPosition
		# Rescale the Hounsfield Units.
		self.image[0].array[self.image[0].array == -2000] = ref.RescaleIntercept
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
		self.image[0].pixelSize = [ref.PixelSpacing[0], ref.PixelSpacing[1], spacingBetweenSlices]
		# CT array extent (from bottom left corner of array); x->Cols, y->Rows z->Depth. (yyxxzz).
		y1 = ref.ImagePositionPatient[1]-0.5*self.image[0].pixelSize[1] 
		y2 = ref.ImagePositionPatient[1]-0.5*self.image[0].pixelSize[1] + shape[0]*self.image[0].pixelSize[1]
		x1 = ref.ImagePositionPatient[0]-0.5*self.image[0].pixelSize[0] 
		x2 = ref.ImagePositionPatient[0]-0.5*self.image[0].pixelSize[0] + shape[1]*self.image[0].pixelSize[0]
		z1 = ref.ImagePositionPatient[2]+0.5*self.image[0].pixelSize[2] - shape[2]*self.image[0].pixelSize[2]
		z2 = ref.ImagePositionPatient[2]+0.5*self.image[0].pixelSize[2] 
		self.extent = np.array([y1,y2,x1,x2,z1,z2])

		# GPU drivers.
		gpu = gpuInterface()
		# Patient imaging orientation. (Rotation happens in [row,col,depth]).
		if self.image[0].patientPosition == 'HFS':
			# Head First, Supine.
			# Rotate to look through the LINAC gantry in it's home position. I.e. the patient in the seated position at the IMBL.
			kwargs = (
				(0,-90,0),
				(0,0,0),
				self.image[0].pixelSize,
				None,
				None
				)
		# elif self.patientPosition == 'HFP':
		# 	pass
		# elif self.patientPosition == 'FFS':
		# 	pass
		# elif self.patientPosition == 'FFP':
		# 	pass
		else:
			# Special case for sitting objects on CT table in upright position (essentially a sitting patient).
			print('Executed special case for CT import. Its not HFS/FFS or anything usual.')
			# self.array, self.arrayExtent = gpu.rotate(155,-90,0,)
			# self.array = gpu.rotate(0,-90,0,)
			kwargs = (
				(0,-90,0),
				(0,0,0),
				self.image[0].pixelSize,
				None,
				None
				)

		# Run the gpu rotation.
		self.image[0].array = gpu.rotate(self.image[0].array,*kwargs)
		# Update other variables from gpu.
		self.image[0].pixelSize = gpu.pixelSize
		self.image[0].extent = gpu.extent

		# Save and write fp and ds.
		np.save(self.fp+'/ct0.npy',self.image[0].array)
		self.image[0].ds = [self.fp+'/ct0.npy']
		self.image[0].fp = os.path.dirname(self.image[0].ds[0])

	def importXR(self):
		# Create an image list.
		self.image = [image(),image()]
		# Read in hdf5 image arrays.
		file = h5py.File(self.ds[0],'r')
		# Ensure it has two images.
		if file.attrs['NumberOfImages'] != 2: 
			print('HDF5 file must contain only two images.')
			return
		self.image[0].array = file['0'][:]
		self.image[1].array = file['1'][:]
		print('In File:')
		print(self.image[0].array)
		# Extract the extent information, should be available in image.
		self.image[0].extent = file['0'].attrs['extent']
		self.image[1].extent = file['1'].attrs['extent']
		# Image isocenter (typically the beam isocenter).
		self.image[0].isocenter = file['0'].attrs['isocenter']
		self.image[1].isocenter = file['1'].attrs['isocenter']

	def importRTPLAN(self):
		# Firstly, read in DICOM file.
		ref = dicom.read_file(self.ds[0])
		# Set file path.
		self.fp = os.path.dirname(self.ds[0])
		# We are reading in a RTPLAN DICOM file.
		self.patientName = ref.PatientName
		# Construct an object array of the amount of beams to be delivered.
		self.image = np.empty(ref.FractionGroupSequence[0].NumberOfBeams,dtype=object)
		# Load the CT Data.
		# ctArray = np.load(ctData.array)
		# Do some GPU shit.
		# gpu = gpuInterface()
		# gpu.copyTexture(ctArray,extent=ctData.arrayExtent,pixelSize=ctData.pixelSize)

		# Extract confromal mask data.
		for i in range(len(self.image)):
			# self.image[i].block = np.empty(ref.BeamSequence[i].NumberOfBlocks,dtype=object)
			self.image[i].mask = ref.BeamSequence[i].BlockSequence[0].BlockData
			self.image[i].maskThickness = ref.BeamSequence[i].BlockSequence[0].BlockThickness

			# Beam limiting device angle (collimator rotation angle) of Clinical LINAC. Rotation about BEV.
			test = float(ref.BeamSequence[i].ControlPointSequence[0].BeamLimitingDeviceAngle)
			if 181 < test < 359:
				# Turn into a negative angle > -180.
				self.image[i].collimator = -360+test
			else:
				# It is within 0-180 deg and can remain a positive value. 
				self.image[i].collimator = test	

			# Gantry Angle of Clinical LINAC. Rotation about DICOM Z-axis.
			test = float(ref.BeamSequence[i].ControlPointSequence[0].GantryAngle)
			if 181 < test < 359:
				# Turn into a negative angle > -180.
				self.image[i].gantry = -360+test
			else:
				# It is within 0-180 deg and can remain a positive value. 
				self.image[i].gantry = test

			# Patient support angle (table rotation angle) of Clinical LINAC. Rotation about DICOM Y-axis.
			test = float(ref.BeamSequence[i].ControlPointSequence[0].PatientSupportAngle)
			if 181 < test < 359:
				# Turn into a negative angle > -180.
				self.image[i].patientSupport = -360+test
			else:
				# It is within 0-180 deg and can remain a positive value. 
				self.image[i].patientSupport = test	

			# self.image[i].pitchAngle = float(ref.BeamSequence[i].ControlPointSequence[0].TableTopPitchAngle)
			# self.image[i].rollAngle = float(ref.BeamSequence[i].ControlPointSequence[0].TableTopRollAngle)

			self.image[i].isocenter = np.array(ref.BeamSequence[i].ControlPointSequence[0].IsocenterPosition)
			# Rearrange xyz to match imported CT.
			self.image[i].isocenter[0],self.image[i].isocenter[1],self.image[i].isocenter[2] = self.image[i].isocenter[2],self.image[i].isocenter[0],self.image[i].isocenter[1]
			# Consider updating isocenter parameter before each rotation:
			gpu.isocenter = np.array(self.image[i].isocenter)

			# Apply euler rotations. Collimator first (variable rotation axis, z), then gantry (fixed x), then table (fixed z).
			# array, self.image[i].arrayExtent = gpu.rotate(-self.image[i].gantryAngle,0,-self.image[i].patientSupportAngle,order='pat-gant-col',z1=-self.image[i].collimatorAngle)
			array, self.image[i].arrayExtent = gpu.rotate(self.image[i].gantryAngle,0,self.image[i].patientSupportAngle,order='pat-gant-col',z1=self.image[i].collimatorAngle)
			# array, self.image[i].arrayExtent = gpu.rotate(0,0,90,order='pat-gant-col',z1=0)
			# Get back new isoc location.
			self.image[i].isocenter = gpu.isocenter

			# Hold file path to each plot and save.
			self.image[i].array = self.path+'/image%i'%(i+1)+'_array.npy'
			np.save(self.image[i].array, array)