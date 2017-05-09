from epics import PV

''' 
CLASS USE:
system = hutch2b_mrt()

system.V.get()
system.V.put(num)
system.V.info
system.V.monitor() etc.
'''


class hutch2b_mrt:
	''' Class that controls the MRT motors in Hutch 2B. '''
	def __init__(self):
		''' Setup generic 6 DoF motor process variables (PVs) for MRT stage. '''
		self.tx = PV('V:m1.VAL')
		self.ty = PV('h1:m1.VAL')
		self.tz = PV('h2:m1.VAL')
		self.rx = False
		self.ry = PV('rotV:m1.VAL')
		self.rz = False

		''' Setup specific motor PV's. '''
		self.TableZ = PV('TableZ:m1.VAL')

	def monitorAll(state):
		if state != (True or False):
			state = False

		self.monitorAllMotors = state

		