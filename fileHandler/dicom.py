import dicom
import numpy as np
import os
from scipy import ndimage
from skimage.external import tifffile as tiff
from scipy.interpolate import interp1d
from syncmrt.tools.cuda import gpuInterface
from syncmrt import fileHandler
from natsort import natsorted

def importDicom(ds,modality):
	files = []
	for i in range(len(ds)):
		testFile = dicom.read_file(ds[i])
		if testFile.Modality == modality:
			files.append(ds[i])
		else:
			pass

	return natsorted(files)

class importCT:
	def __init__(self,ds,arrayFormat='npy'):
		'''importCT: Import the CT dataset and all it's relevant DICOM tags.'''
		# Set list of filenames for dataset, reference file (first file in stack) and the filepath to the folder containing the dataset.
		self.ds = ds
		self.path = os.path.dirname(ds[0])
		self.ref = dicom.read_file(self.ds[0])

		# Specify the array format to save in. Typically this is a numpy array, tif's or jpg's are possible but not built in.
		self.format = arrayFormat

		# Dimensions are based on rows and cols in reference file, and the number of files in the dataset.
		ctArrayDimensions = np.array([int(self.ref.Rows), int(self.ref.Columns), len(self.ds)])

		# Make numpy array of -1000 HU (air), this should be the size of the 3d volume.
		self.ctArray = np.zeros(ctArrayDimensions, dtype=np.result_type(self.ref.pixel_array))-1000

		# For each slice extract the pixel data and put in respective z slice in array. 
		for fn in self.ds:
			data = dicom.read_file(fn)
			self.ctArray[:,:,ctArrayDimensions[2]-self.ds.index(fn)-1] = data.pixel_array

		# Get the patient orientation.
		self.patientPosition = self.ref.PatientPosition

		# Patient setup variables.
		self.imageOrientationPatient = self.ref.ImageOrientationPatient
		self.imagePositionPatient = self.ref.ImagePositionPatient

		# HU vars.
		self.rescaleType = self.ref.RescaleType
		self.rescaleSlope = self.ref.RescaleSlope
		self.rescaleIntercept = self.ref.RescaleIntercept
		self.rescaleHU()

		# Sometimes the spacing between slices tag doesn't exist, if it doesn't, create it.
		try:
			self.spacingBetweenSlices = self.ref.SpacingBetweenSlices
		except:
			start = self.ref.ImagePositionPatient[2]
			file = dicom.read_file(self.ds[-1])
			end = file.ImagePositionPatient[2]

			self.spacingBetweenSlices = abs(end-start)/(len(self.ds)-1)

		# Voxel shape determined by detector element sizes and CT slice thickness.
		self.pixelSize = np.array([self.ref.PixelSpacing[0], self.ref.PixelSpacing[1], self.spacingBetweenSlices])

		# CT array extent (from bottom left corner of array); x->Cols, y->Rows z->Depth.
		x1 = self.imagePositionPatient[0]-0.5*self.pixelSize[0]
		x2 = self.imagePositionPatient[0]-0.5*self.pixelSize[0] + self.ctArray.shape[1]*self.pixelSize[0]
		y1 = self.imagePositionPatient[1]-0.5*self.pixelSize[1]
		y2 = self.imagePositionPatient[1]-0.5*self.pixelSize[1] + self.ctArray.shape[0]*self.pixelSize[1]
		z1 = self.imagePositionPatient[2]+0.5*self.pixelSize[2] - self.ctArray.shape[2]*self.pixelSize[2]
		z2 = self.imagePositionPatient[2]+0.5*self.pixelSize[2]
		self.ctExtent = np.array([x1,x2,y1,y2,z1,z2])

		# GPU drivers.
		gpu = gpuInterface()
		gpu.copyTexture(self.ctArray,pixelSize=self.pixelSize,extent=self.ctExtent)

		# Patient imaging orientation. (Rotation happens in [row,col,depth]).
		if self.patientPosition == 'HFS':
			# Head First, Supine.
			# Rotate to look through the LINAC gantry in it's home position. I.e. the patient in the seated position at the IMBL.
			self.array, self.arrayExtent = gpu.rotate(0,90,0)
		elif self.patientPosition == 'HFP':
			pass
		elif self.patientPosition == 'FFS':
			pass
		elif self.patientPosition == 'FFP':
			pass
		else:
			# Special case for sitting objects on CT table in upright position (essentially a sitting patient).
			print('Executed special case in syncmrt.fileHandler.dicom.py')
			self.array, self.arrayExtent = gpu.rotate(0,-90,0)

		self.pixelSize = gpu.pixelSize

		# Save
		self.save3D(['ct0_dicom','ct1_correctlyOrientated'])

	def rescaleHU(self):
		# Rescale the Hounsfield Units.
		# self.ctArray = self.ctArray*self.rescaleSlope + self.rescaleIntercept
		self.ctArray[self.ctArray == -2000] = 0

	'''
	def flatten(self):
		# Flatten the images along the z axis.
		self.flat = np.sum(self.normal,axis=2)
		self.flat90 = np.sum(self.orthogonal,axis=2)

	def save2D(self,fn0,fn90):
		# Save 2D arrays as numpy files. If no format specified then save as TIFF: should be avoided. 
		self.flatten()
		if self.format == 'npy':
			np.save(self.path+'/'+fn0+'.'+self.format, self.flat)
			np.save(self.path+'/'+fn90+'.'+self.format, self.flat90)
		else:
			tiff.imsave(self.path+'/'+fn0+'.'+self.format, self.flat.astype('float32'))
			tiff.imsave(self.path+'/'+fn90+'.'+self.format, self.flat90.astype('float32'))
	'''

	def save3D(self,fn):
		# Save as file.
		if self.format == 'npy':
			np.save(self.path+'/'+fn[0]+'.'+self.format, self.ctArray)
			np.save(self.path+'/'+fn[1]+'.'+self.format, self.array)
		else:
			print('Cannot save 3D images, must be numpy filetype.')

class importRTP:
	def __init__(self,ds):
		'''Only accepts dicom files.'''
		self.rtp = None
		dicomData = dicom.read_file(ds[0])

		if dicomData.Modality == 'RTPLAN':
			self.rtp = dicomData
			self.path = os.path.dirname(ds[0])
		else:
			print("Error reading Treatment Plan file.")

		# Check for an accompanying RS file?

	def extractTreatmentBeams(self,ctData):
		'''Iterate through number of beams and rotate ct data to match beam view.'''
		self.beam = np.empty(self.rtp.FractionGroupSequence[0].NumberOfBeams,dtype=object)

		ctArray = np.load(ctData.array)
		gpu = gpuInterface()
		gpu.copyTexture(ctArray,extent=ctData.arrayExtent,pixelSize=ctData.pixelSize)

		# Assume single control point sequence...
		for i in range(len(self.beam)):
			self.beam[i] = fileHandler.dataBeam()
			self.beam[i].numberOfBlocks = np.empty(self.rtp.BeamSequence[i].NumberOfBlocks,dtype=object)
			self.beam[i].blockData = self.rtp.BeamSequence[i].BlockSequence[0].BlockData
			self.beam[i].blockThickness = self.rtp.BeamSequence[i].BlockSequence[0].BlockThickness

			# Beam limiting device angle (collimator rotation angle) of Clinical LINAC. Rotation about BEV.
			test = float(self.rtp.BeamSequence[i].ControlPointSequence[0].BeamLimitingDeviceAngle)
			if 181 < test < 359:
				# Turn into a negative angle > -180.
				self.beam[i].collimatorAngle = -360+test
			else:
				# It is within 0-180 deg and can remain a positive value. 
				self.beam[i].collimatorAngle = test	

			# Gantry Angle of Clinical LINAC. Rotation about DICOM Z-axis.
			test = float(self.rtp.BeamSequence[i].ControlPointSequence[0].GantryAngle)
			if 181 < test < 359:
				# Turn into a negative angle > -180.
				self.beam[i].gantryAngle = -360+test
			else:
				# It is within 0-180 deg and can remain a positive value. 
				self.beam[i].gantryAngle = test

			# Patient support angle (table rotation angle) of Clinical LINAC. Rotation about DICOM Y-axis.
			test = float(self.rtp.BeamSequence[i].ControlPointSequence[0].PatientSupportAngle)
			if 181 < test < 359:
				# Turn into a negative angle > -180.
				self.beam[i].patientSupportAngle = -360+test
			else:
				# It is within 0-180 deg and can remain a positive value. 
				self.beam[i].patientSupportAngle = test	

			# self.beam[i].pitchAngle = float(self.rtp.BeamSequence[i].ControlPointSequence[0].TableTopPitchAngle)
			# self.beam[i].rollAngle = float(self.rtp.BeamSequence[i].ControlPointSequence[0].TableTopRollAngle)

			self.beam[i].isocenter = np.array(self.rtp.BeamSequence[i].ControlPointSequence[0].IsocenterPosition)
			# Rearrange xyz to match imported CT.
			self.beam[i].isocenter[0],self.beam[i].isocenter[1],self.beam[i].isocenter[2] = self.beam[i].isocenter[2],self.beam[i].isocenter[0],self.beam[i].isocenter[1]
			# Consider updating isocenter parameter before each rotation:
			gpu.isocenter = np.array(self.beam[i].isocenter)

			# Apply euler rotations. Collimator first (variable rotation axis, z), then gantry (fixed x), then table (fixed z).
			# Rotations happen in CCW directions.
			array, self.beam[i].arrayExtent = gpu.rotate(self.beam[i].gantryAngle,0,-self.beam[i].patientSupportAngle,order='zxz',z1=-self.beam[i].collimatorAngle)
			# Get back new isoc location.
			self.beam[i].isocenter = gpu.isocenter

			# Hold file path to each plot and save.
			self.beam[i].array = self.path+'/beam%i'%(i+1)+'_array.npy'
			np.save(self.beam[i].array, array)