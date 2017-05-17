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

		# GPU drivers.
		gpu = gpuInterface()
		gpu.copyTexture(self.arr,self.pixelSize)

		# Patient imaging orientation. (Rotation happens in [row,col,depth]).
		if self.orientation == 'HFS':
			# Head First, Supine.
			# Rotate to look through the LINAC gantry in it's home position. I.e. the patient in the seated position at the IMBL.
			self.rot, self.pix0 = gpu.rotate(0,90,0)
			self.rot90, self.pix90  = gpu.rotate(90,90,0)
			# Set matching extent (in mm) for 2D plot in DRR.
			left = self.ref.ImagePositionPatient[0]+self.ref.Rows*self.ref.PixelSpacing[0]
			right = self.ref.ImagePositionPatient[0]
			bottom = self.ref.ImagePositionPatient[2]-(self.dims[2]-1)*self.spacingBetweenSlices
			top = self.ref.ImagePositionPatient[2]
			self.normalExtent = np.array([left,right,bottom,top])
			# Set matching extent (in mm) for 2D plot in DRR.
			left = self.ref.ImagePositionPatient[1]
			right = self.ref.ImagePositionPatient[1]+self.ref.Rows*self.ref.PixelSpacing[1]
			bottom = self.ref.ImagePositionPatient[2]-(self.dims[2]-1)*self.spacingBetweenSlices
			top = self.ref.ImagePositionPatient[2]
			self.orthogonalExtent = np.array([left,right,bottom,top])
		elif self.orientation == 'HFP':
			self.rot, self.pix0 = gpu.rotate(0,-90,0)
			self.rot90, self.pix90  = gpu.rotate(0,-180,0)
		elif self.orientation == 'FFS':
			self.rot, self.pix0 = gpu.rotate(-90,0,180)
			self.rot90, self.pix90 = gpu.rotate(-180,0,180)
		elif self.orientation == 'FFP':
			self.rot, self.pix0 = gpu.rotate(-90,180,180)
			self.rot90, self.pix90  = gpu.rotate(-180,180,180)
		else:
			# Special case for sitting objects on CT table in upright position (essentially a sitting patient).
			print('Executed special case in syncmrt.fileHandler.dicom.py')
			self.rot, self.pix0 = gpu.rotate(-90,0,0)
			self.rot90, self.pix90 = gpu.rotate(-90,90,0)

		# Save
		# self.save2D('ct_0deg','ct_90deg')
		self.save3D(['ct_3d','ct_normal','ct_orthogonal'])

	def rescaleHU(self):
		# Rescale the Hounsfield Units.
		# self.arr = self.arr*self.rescaleSlope + self.rescaleIntercept
		self.arr[self.arr == -2000] = 0

	def flatten(self):
		# Flatten the images along the z axis.
		self.flat = np.sum(self.rot,axis=2)
		self.flat90 = np.sum(self.rot90,axis=2)

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
			np.save(self.path+'/'+fn[1]+'.'+self.format, self.rot)
			np.save(self.path+'/'+fn[2]+'.'+self.format, self.rot90)
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

	def extractTreatmentBeams(self,ctArray,pixelSize):
		'''Iterate through number of beams and rotate ct data to match beam view.'''
		self.beam = np.empty(self.rtp.FractionGroupSequence[0].NumberOfBeams,dtype=object)

		array = np.load(ctArray)
		gpu = gpuInterface()
		gpu.copyTexture(array,pixelSize)

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

			# # Normal view extent for plotting (in mm),
			# left = self.ref.ImagePositionPatient[0]
			# right = self.ref.ImagePositionPatient[0]+self.ref.Rows*self.ref.PixelSpacing[0]
			# bottom = self.ref.ImagePositionPatient[2]-(self.dims[2]-1)*self.spacingBetweenSlices
			# top = self.ref.ImagePositionPatient[2]
			# self.normalExtent = np.array([left,right,bottom,top])
			# # Orthogonal view extent for plotting (in mm),
			# left = self.ref.ImagePositionPatient[0]
			# right = self.ref.ImagePositionPatient[0]+self.ref.Rows*self.ref.PixelSpacing[0]
			# bottom = self.ref.ImagePositionPatient[2]-(self.dims[2]-1)*self.spacingBetweenSlices
			# top = self.ref.ImagePositionPatient[2]
			# self.orthogonalExtent = np.array([left,right,bottom,top])

			# Apply euler rotations (x,y,z).
			arrayNormal, self.beam[i].arrayNormalPixelSize = gpu.rotate(float(-4.97),float(0),float(-90),order='zxz',z1=float(90))
			# Save, reload onto to GPU, or find a way to use current GPU results to work off.
			arrayOrthogonal, self.beam[i].arrayOrthogonalPixelSize = gpu.rotate(90,0,0)

			# arrayNormal, self.beam[i].arrayNormalPixelSize = gpu.rotate(float(0),self.beam[i].patientSupportAngle,self.beam[i].gantryAngle,order='yzx')
			# arrayOrthogonal, self.beam[i].arrayOrthogonalPixelSize = gpu.rotate(self.beam[i].collimatorAngle,self.beam[i].patientSupportAngle,self.beam[i].gantryAngle,order='yzx')
			

			# # Didn't change pixel size??? Why does it work???
			# self.beam[i].arrayNormalPixelSize = pixelSize
			# self.beam[i].arrayOrthogonalPixelSize = pixelSize

			# Hold file path to each plot and save.
			self.beam[i].arrayNormal = self.path+'/beam%i'%(i+1)+'normal.npy'
			self.beam[i].arrayOrthogonal = self.path+'/beam%i'%(i+1)+'orthogonal.npy'

			np.save(self.beam[i].arrayNormal, arrayNormal)
			np.save(self.beam[i].arrayOrthogonal, arrayOrthogonal)