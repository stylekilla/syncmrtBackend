import os
import pydicom as dicom
import numpy as np
from synctools.fileHandler.image import image2d, image3d
from natsort import natsorted
from synctools.tools.opencl import gpu as gpuInterface
import h5py
import logging

'''
The importer class takes DICOM/HDF5 images and turns them into a
	class (image2d or image3d) for plotting in QsWidgets.QPlot().
	This is where we disconnect the DICOM information and take
	only what the internals of SyncMRT requires to operate. Maybe
	in the future such integrations could just see the use of
	DICOM throughout but then things would have to be re-written
	to understand DICOM. This is just currently my own interface.
Think of this class as the interface to QPlot. As such it should
	probably be packaged with it.
'''

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
			self.image.append(image2d())
			self.image[i].pixelArray = file[str(i)][:]
			# Extract the extent information, should be available in image.
			self.image[i].extent = file[str(i)].attrs['extent']
			# Patient isocenter (typically the beam isocenter).
			self.image[i].patientIsocenter = file[str(i)].attrs['isocenter']
			# Import image view.
			# self.image[i].view = file[str(i)].attrs['view']
			# self.image[i].axis = file[str(i)].attrs['axis']
			self.image[i].view = {
					'title':'AP',
					'xLabel':'LR',
					'yLabel':'SI',
				}
			self.image[i].orientation = [1,2,0]

	def checkDicomModality(self,modality):
		# Start with empty list of files.
		files = {}
		for i in range(len(self.ds)):
			# Read the file in.
			testFile = dicom.dcmread(self.ds[i])
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

	def importCT(self):
		# We are reading in a CT DICOM file.
		ref = dicom.dcmread(self.ds[0])
		# Get CT shape.
		shape = np.array([int(ref.Columns), int(ref.Rows), len(self.ds)])
		# Initialize image with array of zeros.
		self.ctDataset = image3d()
		self.ctDataset.pixelArray = np.zeros(shape, dtype=np.int16)
		# self.ctDataset.pixelArray = np.zeros(shape, dtype=np.int32)
		# Read array in one slice at a time.
		for fn in self.ds:
			slice = dicom.dcmread(fn)
			self.ctDataset.pixelArray[:,:,shape[2]-self.ds.index(fn)-1] = slice.pixel_array
			# Should send signal of import status here.
			# pct = self.ds.index(fn)/len(self.ds)
			# progress.emit(pct)
		# Rescale the Hounsfield Units.
		self.ctDataset.pixelArray = (self.ctDataset.pixelArray*ref.RescaleSlope) + ref.RescaleIntercept
		# Get the extent details of the dataset.
		# CT array extent NP(l,r,b,t,f,b)
		verticesPatient1 = [
			[0,0,0,1],
			[ref.Columns-1,0,0,1],
			[0,ref.Rows-1,0,1],
			[ref.Columns-1,ref.Rows-1,0,1]
		]
		verticesPatient2 = [
			[0,0,len(self.ds)-1,1],
			[ref.Columns-1,0,len(self.ds)-1,1],
			[0,ref.Rows-1,len(self.ds)-1,1],
			[ref.Columns-1,ref.Rows-1,len(self.ds)-1,1],
		]
		# Get the image plane attributes.
		pix = list(map(float, ref.PixelSpacing))
		ori = list(map(int, ref.ImageOrientationPatient))
		pos1 = list(map(float, dicom.dcmread(self.ds[-1]).ImagePositionPatient))
		pos2 = list(map(float, ref.ImagePositionPatient))
		# Get the patient vertices for the first and last slice.
		# M, is from eqn C.7.6.2.1-1 in the DICOM Image Plane Module.
		verticesPatient = []
		M = np.array([
			[ori[0]*pix[0],	ori[3]*pix[1],	0,	pos1[0]],
			[ori[1]*pix[0],	ori[4]*pix[1],	0,	pos1[1]],
			[ori[2]*pix[0],	ori[5]*pix[1],	0,	pos1[2]],
			[0,				0,				0,	1]
		])
		for vertice in verticesPatient1:
			verticesPatient.append(np.array(M@np.transpose(vertice)))
		M = np.array([
			[ori[0]*pix[0],	ori[3]*pix[1],	0,	pos2[0]],
			[ori[1]*pix[0],	ori[4]*pix[1],	0,	pos2[1]],
			[ori[2]*pix[0],	ori[5]*pix[1],	0,	pos2[2]],
			[0,				0,				0,	1]
		])
		for vertice in verticesPatient2:
			verticesPatient.append(np.array(M@np.transpose(vertice)))
		# Create a singular array.
		verticesPatient = np.array(verticesPatient)
		# Create generic vertices to map to the patient position. 
		vertices = np.array([
			[0,0,0],
			[ref.Columns-1,0,0],
			[0,ref.Rows,0],
			[ref.Columns-1,ref.Rows,0],
			[0,0,len(self.ds)-1],
			[ref.Columns-1,0,len(self.ds)-1],
			[0,ref.Rows,len(self.ds)-1],
			[ref.Columns-1,ref.Rows,len(self.ds)-1]
		])
		M = np.array([
			[ori[0]*pix[0],	ori[3]*pix[1],	1],
			[ori[1]*pix[0],	ori[4]*pix[1],	1],
			[ori[2]*pix[0],	ori[5]*pix[1],	1],
		])
		verticesAligned = []
		for p in vertices:
			verticesAligned.append(np.array(M@np.transpose(p)))
		# Turn into a single array.
		verticesAligned = np.array(verticesAligned)
		# Find the minimum and maximum points in the vertices.
		xn, yn, zn = np.argmin(verticesAligned,axis=0)
		xp, yp, zp = np.argmax(verticesAligned,axis=0)
		# Find Minimum Point in X:
		x1 = verticesPatient[xn,0] + np.sign(xp-xn)*(np.absolute(xp-xn)/ref.Columns)
		x2 = verticesPatient[xp,0] + np.sign(xp-xn)*(np.absolute(xp-xn)/ref.Columns)
		y1 = verticesPatient[yp,1] + np.sign(yp-yn)*(np.absolute(yp-yn)/ref.Rows)
		y2 = verticesPatient[yn,1] + np.sign(yp-yn)*(np.absolute(yp-yn)/ref.Rows)
		z1 = verticesPatient[zp,2] + np.sign(zp-zn)*(np.absolute(zp-zn)/len(self.ds))
		z2 = verticesPatient[zn,2] + np.sign(zp-zn)*(np.absolute(zp-zn)/len(self.ds))
		self.extent = np.array([x1,x2,y1,y2,z1,z2])
		# Start gpu context.
		gpu = gpuInterface()
		# Load array onto GPU.
		gpu.loadData(self.ctDataset.pixelArray)
		# Get current CT orientation.
		self.ctDataset.orientation = ref.ImageOrientationPatient
		# Create a 2d image list for plotting.
		self.image = [image2d(),image2d()]
		# Flatten the 3d image to the two 2d images.
		self.image[0].pixelArray = np.sum(self.ctDataset.pixelArray,axis=2)
		self.image[0].extent = np.array([ self.extent[0], self.extent[1], self.extent[2], self.extent[3] ])
		self.image[1].pixelArray = np.fliplr(np.sum(self.ctDataset.pixelArray,axis=1))
		self.image[1].extent = np.array([ self.extent[4], self.extent[5], self.extent[2], self.extent[3] ])

		# Sometimes the spacing between slices tag doesn't exist, if it doesn't, create it.
		# try:
		# 	spacingBetweenSlices = ref.SpacingBetweenSlices
		# except:
		# 	logging.debug('Assuming that the CT has equally spaced slices.')
		# 	start = ref.ImagePositionPatient[2]
		# 	file = dicom.dcmread(self.ds[-1])
		# 	end = file.ImagePositionPatient[2]
		# 	spacingBetweenSlices = abs(end-start)/(len(self.ds)-1)
		# # Voxel shape determined by detector element sizes and CT slice thickness.
		# self.image[0].pixelSize = [ref.PixelSpacing[0], -ref.PixelSpacing[1], spacingBetweenSlices]
		# # Note the axes that we are working on, these will change as we work.
		# self.image[0].orientation = np.array([0,1,2])



		# Assume (0020,0037) Image Orientation (Patient): 1\0\0\0\1\0
		patientVector = None
		if list(map(int,ref.ImageOrientationPatient)) == [1,0,0,0,1,0]:
			# patientVector describes cosines of FH / LR -> x,y,z axes.
			if ref.PatientPosition == 'HFS': patientVector = [0,0,1,-1,0,0]
			if ref.PatientPosition == 'FFS': patientVector = [0,0,-1,1,0,0]
			if ref.PatientPosition == 'HFP': patientVector = [0,0,1,1,0,0]
			if ref.PatientPosition == 'FFP': patientVector = [0,0,-1,-1,0,0]
		else:
			logging.critical('Cannot process image with patient orientation: ',ref.ImageOrientationPatient)

		patientViews = {}
		# [['xvector'],['yvector'],['zvector']]
		# vector describes the DICOM axes in terms of the python axes.
		# x is column to right
		# y is row to bottom
		# z is depth to back
		patientViews['AP'] = [[1,0,0],[0,0,1],[0,1,0]]
		patientViews['PA'] = [[-1,0,0],[0,0,-1],[0,-1,0]]
		patientViews['LR'] = [[0,0,-1],[1,0,0],[0,-1,0]]
		patientViews['RL'] = [[0,0,1],[-1,0,0],[0,-1,0]]
		patientViews['SI(S)'] = [[-1,0,0],[0,1,0],[0,0,-1]]
		patientViews['SI(P)'] = [[1,0,0],[0,-1,0],[0,0,-1]]
		patientViews['IS(S)'] = [[1,0,0],[0,1,0],[0,0,1]]
		patientViews['IS(P)'] = [[-1,0,0],[0,-1,0],[0,0,1]]

		'''
		Here we orientate the CT data with two assumptions:
			1. The CT was taken in HFS.
			2. At the synchrotron the patient is in an upright position.
		'''

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

		# # Override
		# kwargs = (
		# 	['090'],
		# 	self.image[0].pixelSize,
		# 	self.extent,
		# 	None
		# 	)

		# # Run the gpu rotation.
		# newView = gpu.rotate(self.image[0].array,*kwargs)

		# # Create an image list.
		# self.image[0].pixelArray = np.sum(newView,axis=0)
		# self.image[1].pixelArray = np.sum(newView,axis=1)

		# # Update rotated variables from gpu.
		# # self.image[0].axes = gpu.axes
		# self.image[0].pixelSize = gpu.pixelSize
		# self.image[0].extent = gpu.extent
		# # Set empty isocenter for ct loading, update when rtplan is loaded.
		# self.isocenter = np.array([0,0,0])

		# Save and write fp and ds.
		np.save(self.fp+'/dicom_ct.npy',self.ctDataset.pixelArray)
		self.ctDataset.ds = [self.fp+'/dicom_ct.npy']
		self.ctDataset.fp = os.path.dirname(self.fp)

	def importRTPLAN(self,ctImage):
		# Firstly, read in DICOM rtplan file.
		ref = dicom.dcmread(self.ds[0])
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