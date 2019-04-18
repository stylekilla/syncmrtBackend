from synctools.fileHandler import importer
from synctools.tools.opencl import gpu

class patient:
	def __init__(self,name='Default'):
		self.name = name
		# Program internals.
		self._gpuContext = None
	# Load Patient Data.
	def load(self,dataset,dtype):
		if dtype == 'DX': self.dx = importer.sync_dx(dataset)
		elif dtype == 'CT': 
			# Create a GPU context for the ct array.
			self._gpuContext = gpu()
			self.ct = importer.dicom_ct(dataset,self._gpuContext)
		elif dtype == 'RTPLAN': 
			if self.ct != None: 
				self.rtplan = importer.dicom_rtplan(
						dataset,
						self.ct.RCS,
						self.ct.RCS_LEFTTOP,
						self.ct.pixelArray.shape,
						self.ct.pixelSize,
						self._gpuContext
					)
			else: 
				logging.critical('No CT Dataset loaded. Cannot import treatment plan.')
		else: logging.critical('No importer for file type: ',dtype)
		# self.rtstructure = importer.dicom_rtstructure(dataset)