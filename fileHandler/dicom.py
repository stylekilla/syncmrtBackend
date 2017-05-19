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
		self.dims = np.array([int(self.ref.Rows), int(self.ref.Columns), len(self.ds)])

		# Make numpy array of -1000 HU (air), this should be the size of the 3d volume.
		self.arr = np.zeros(self.dims, dtype=np.result_type(self.ref.pixel_array))-1000

		# For each slice extract the pixel data and put in respective z slice in array. 
		for fn in self.ds:
			data = dicom.read_file(fn)
			self.arr[:,:, self.ds.index(fn)] = np.fliplr(data.pixel_array)

		# Get the patient orientation.
		self.userOrigin = self.ref.ImagePositionPatient
		self.orientation = self.ref.PatientPosition

		# Patient setup variables.
		self.imageOrientationPatient = self.ref.ImageOrientationPatient
		self.imagePositionPatient = self.ref.ImagePositionPatient

		# HU vars.
		self.rescaleType = self.ref.RescaleType
		self.rescaleSlope = self.ref.RescaleSlope
		self.rescaleIntercept = self.ref.RescaleIntercept
		self.rescaleHU()
		# self.patientIsoc = self.ref.PatientIsoc
		try:
			self.spacingBetweenSlices = self.ref.SpacingBetweenSlices
		except:
			start = self.ref.ImagePositionPatient[2]
			file = dicom.read_file(self.ds[-1])
			end = file.ImagePositionPatient[2]

			self.spacingBetweenSlices = abs(end-start)/(len(self.ds)-1)

		self.pixelSize = np.array([self.ref.PixelSpacing[0], self.ref.PixelSpacing[1], self.spacingBetweenSlices])
		# ArrayAxes is a 1x3 array of pixels and their direction.
		self.arrayAxes = np.dot(np.array([[1,0,0],[0,1,0],[0,0,1]]),self.pixelSize)

		# GPU drivers.
		gpu = gpuInterface()
		gpu.copyTexture(self.arr,self.arrayAxes,self.imagePositionPatient)

		# Patient imaging orientation. (Rotation happens in [row,col,depth]).
		if self.orientation == 'HFS':
			# Head First, Supine.
			# Rotate to look through the LINAC gantry in it's home position. I.e. the patient in the seated position at the IMBL.
			self.normal, self.normalAxes,self.normalPosition = gpu.rotate(0,90,0)
			self.orthogonal, self.orthogonalAxes,self.orthogonalPosition = gpu.rotate(90,90,0)
		elif self.orientation == 'HFP':
			pass
		elif self.orientation == 'FFS':
			pass
		elif self.orientation == 'FFP':
			pass
		else:
			# Special case for sitting objects on CT table in upright position (essentially a sitting patient).
			print('Executed special case in syncmrt.fileHandler.dicom.py')
			self.normal, self.normalAxes,self.normalPosition = gpu.rotate(0,-90,0)
			self.orthogonal, self.orthogonalAxes,self.orthogonalPosition = gpu.rotate(90,-90,0)

		# Set matching extent (in mm) for 2D plot in DRR.
		left = self.normalPosition[1]
		right = self.normalPosition[1]+self.normal.shape[1]*self.normalAxes[1]
		bottom = self.normalPosition[0]-self.normal.shape[0]*self.normalAxes[0]
		top = self.normalPosition[0]
		self.normalExtent = np.array([left,right,bottom,top])
		# Set matching extent (in mm) for 2D plot in DRR.
		left = self.orthogonalPosition[1]
		right = self.orthogonalPosition[1]+self.orthogonal.shape[1]*self.orthogonalAxes[1]
		bottom = self.orthogonalPosition[0]-self.orthogonal.shape[0]*self.orthogonalAxes[0]
		top = self.orthogonalPosition[0]
		self.orthogonalExtent = np.array([left,right,bottom,top])

		print('CT normal Extent, shape, position')
		print(self.normal.shape)
		print(self.normalPosition)
		print(self.normalExtent)

		# Save
		self.save3D(['ct_3d','ct_normal','ct_orthogonal'])

	def rescaleHU(self):
		# Rescale the Hounsfield Units.
		# self.arr = self.arr*self.rescaleSlope + self.rescaleIntercept
		self.arr[self.arr == -2000] = 0

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

	def save3D(self,fn):
		# Save as file.
		if self.format == 'npy':
			np.save(self.path+'/'+fn[0]+'.'+self.format, self.arr)
			np.save(self.path+'/'+fn[1]+'.'+self.format, self.normal)
			np.save(self.path+'/'+fn[2]+'.'+self.format, self.orthogonal)
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

	def extractTreatmentBeams(self,ctArray,axes,patientPosition):
		'''Iterate through number of beams and rotate ct data to match beam view.'''
		self.beam = np.empty(self.rtp.FractionGroupSequence[0].NumberOfBeams,dtype=object)

		array = np.load(ctArray)
		gpu = gpuInterface()
		gpu.copyTexture(array,axes,patientPosition)

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
			# self.beam[i].patientSupportAngle = float(self.rtp.BeamSequence[i].ControlPointSequence[0].PatientSupportAngle)
			self.beam[i].isocenter = np.array(self.rtp.BeamSequence[i].ControlPointSequence[0].IsocenterPosition)

			# Apply euler rotations (x,y,z).
			# arrayNormal, self.beam[i].normalAxes,self.beam[i].normalPosition = gpu.rotate(0,4.97,-90,order='zyz',z1=90)
			arrayNormal, self.beam[i].normalAxes,self.beam[i].normalPosition = gpu.rotate(0,0,-90,order='zxz',z1=90)

			# Save, reload onto to GPU, or find a way to use current GPU results to work off??
			arrayOrthogonal, self.beam[i].orthogonalAxes,self.beam[i].orthogonalPosition = gpu.rotate(0,0,-90,order='zyz',z1=90)
			# arrayOrthogonal, self.beam[i].orthogonalAxes,self.beam[i].orthogonalPosition = gpu.rotate(0,-4.97,-90,order='zyz',z1=90)

			# Set matching extent (in mm) for 2D plot in DRR.
			left = self.beam[i].normalPosition[1]
			right = self.beam[i].normalPosition[1]+arrayNormal.shape[1]*self.beam[i].normalAxes[1]
			bottom = self.beam[i].normalPosition[0]-arrayNormal.shape[0]*self.beam[i].normalAxes[0]
			top = self.beam[i].normalPosition[0]
			self.beam[i].normalExtent = np.array([left,right,bottom,top])
			# Set matching extent (in mm) for 2D plot in DRR.
			left = self.beam[i].orthogonalPosition[1]
			right = self.beam[i].orthogonalPosition[1]+arrayOrthogonal.shape[1]*self.beam[i].orthogonalAxes[1]
			bottom = self.beam[i].orthogonalPosition[0]-arrayOrthogonal.shape[0]*self.beam[i].orthogonalAxes[0]
			top = self.beam[i].orthogonalPosition[0]
			self.beam[i].orthogonalExtent = np.array([left,right,bottom,top])

			print('Normal shape,pos,extn')
			print(arrayNormal.shape)
			print(self.beam[i].normalPosition)
			print(self.beam[i].normalExtent)
			print('Orthogonal shape,pos,extn')
			print(arrayOrthogonal.shape)
			print(self.beam[i].orthogonalPosition)
			print(self.beam[i].orthogonalExtent)

			# Hold file path to each plot and save.
			self.beam[i].arrayNormal = self.path+'/beam%i'%(i+1)+'normal.npy'
			self.beam[i].arrayOrthogonal = self.path+'/beam%i'%(i+1)+'orthogonal.npy'

			np.save(self.beam[i].arrayNormal, arrayNormal)
			np.save(self.beam[i].arrayOrthogonal, arrayOrthogonal)