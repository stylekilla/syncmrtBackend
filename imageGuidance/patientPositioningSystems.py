from epics import PV

''' 
CLASS USE:
system = hutch2b_mrt()

system.V.get()
system.V.put(num)
system.V.info
system.V.monitor() etc.
'''


class DynMRT:
	''' Class that controls the MRT motors in Hutch 2B. '''
	def __init__(self):
		''' Setup generic 6 DoF motor process variables (PVs) for MRT stage. '''
		# self.tx = PV('SR08ID01SST25:SAMPLEH1.VAL')
		# self.ty = PV('SR08ID01SST25:SAMPLEHV.VAL')
		# self.tz = PV('SR08ID01SST25:SAMPLEH2.VAL')
		# self.rx = False
		# self.ry = PV('SR08ID01SST25:ROTATION.VAL')
		# self.rz = False

		self.mrt = []
		try:
			self.mrt['tx'] = PV('SR08ID01SST25:SAMPLEH1.VAL')
			self.mrt['ty'] = PV('SR08ID01SST25:SAMPLEV.VAL')
			self.mrt['tz'] = PV('SR08ID01SST25:SAMPLEH2.VAL')
			self.mrt['ry'] = PV('SR08ID01SST25:ROTATION.VAL')
		except:
			print("Cannot connect to motors.")

	def write(self,pv,value):
		'''Ensure inputs are of correct types, converting float to 3 dec places (0.001 mm)'''
		pv = str(pv)
		value = round(float(value),3)
		if pv in self.mrt:
			self.mrt[pv].put(value)
		else:
			print('Attempting to move non-existant motor',pv,'.')

	def read(self):
		pass