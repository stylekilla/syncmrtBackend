from synctools.fileHandler import importFiles

class patient:
	def __init__(self,name='Default'):
		self.name = name
	# Load Patient Data.
	def loadCT(self,dataset):
		self.ct = importFiles(dataset,modality='CT')
	def loadMRI(self,dataset):
		self.mri = importFiles(dataset,modality='MR')
	def loadRTPLAN(self,dataset,ctImage):
		self.rtplan = importFiles(dataset,modality='RTPLAN',ctImage=ctImage)
	def loadXR(self,dataset):
		self.xr = importFiles(dataset,modality='XR')