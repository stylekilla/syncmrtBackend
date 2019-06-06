from synctools.fileHandler import importer
from synctools.fileHandler import hdf5
from synctools.tools.opencl import gpu
import logging

class patient:
	def __init__(self,name='Default'):
		self.name = name
		self.dx = None
		# Program internals.
		self._gpuContext = None
	# Load Patient Data.
	def load(self,dataset,modality):
		if modality == 'DX': 
			# Close the open one first.
			print(self.dx)
			if self.dx != None: self.dx.close() 
			# Now open the dataset.
			self.dx = importer.sync_dx(dataset)
		elif modality == 'CT': 
			# Create a GPU context for the ct array.
			self._gpuContext = gpu()
			self.ct = importer.dicom_ct(dataset,self._gpuContext)
		elif modality == 'RTPLAN': 
			if self.ct != None: 
				self.rtplan = importer.dicom_rtplan(
						dataset,
						self.ct.RCS,
						self.ct.leftTopFront,
						self.ct.pixelArray.shape,
						self.ct.pixelSize,
						self.ct.patientPosition,
						self._gpuContext
					)
			else: 
				logging.critical('No CT Dataset loaded. Cannot import treatment plan.')
		else: logging.critical('No importer for file type: ',modality)
		# self.rtstructure = importer.dicom_rtstructure(dataset)

	def new(self,fp,modality):
		if modality == 'DX':
			self.dx = hdf5.new(fp)