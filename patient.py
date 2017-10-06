import syncmrt.fileHandler.dataset as ds

class patient:
	def __init__(self,name='Default'):
		self.name = name
	# Load Patient Data.
	def loadCT(self,dataset):
		self.ct = ds(dataset,modality='CT')
	def loadMRI(self,dataset):
		self.mri = ds(dataset,modality='MR')
	def loadRTPLAN(self,dataset):
		self.rtplan = ds(dataset,modality='RTPLAN')
	def loadXR(self,dataset):
		self.xr = ds(dataset,modality='XR')