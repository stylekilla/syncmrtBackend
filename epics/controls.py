import epics
import numpy as np

class robot:
	def __init__(self,pv):
		# Internal vars.
		self._pv = pv
		# PV vars for point of rotation.
		self.pv = {}
		self.pv['x'] = False
		self.pv['y'] = False
		self.pv['z'] = False
		# Set to False to start.
		self._connected = False
		# Connect the PV's
		self._connectPVs()


class motor:
	def __init__(self,pv):
		# Internal vars.
		self._pv = pv
		# PV vars.
		self.pv = {}
		self.pv['RBV'] = False
		self.pv['VAL'] = False
		self.pv['TWV'] = False
		self.pv['TWR'] = False
		self.pv['TWF'] = False
		self.pv['DMOV'] = False
		# Set to False to start.
		self._connected = False
		# Connect the PV's
		self._connectPVs()

	def _connectPVs(self):
		# Record PV root information and connect to motors.
		try:
			# Read Back Value
			self.pv['RBV'] = epics.PV(self._pv+'.RBV')
		except:
			pass
		try:
			# Is motor moving?
			self.pv['DMOV'] = epics.PV(self._pv+'.DMOV')
		except:
			pass
		try:
			# Value to put to motor
			self.pv['VAL'] = epics.PV(self._pv+'.VAL')
		except:
			pass
		try:
			# Tweak Value
			self.pv['TWV'] = epics.PV(self._pv+'.TWV')
		except:
			pass
		try:
			# Tweak Reverse
			self.pv['TWR'] = epics.PV(self._pv+'.TWR')
		except:
			pass
		try:
			# Tweak Forward
			self.pv['TWF'] = epics.PV(self._pv+'.TWF')
		except:
			pass
		# Iterate over all PV's and see if any are disconnected. If one is disconnected, set the state to False.
		# If everything passes, set the state to True.
		state = True
		for key in self.pv:
			if self.pv[key] is False: state = False
		self._connected = state

	def readValue(self,attribute):
		if self._connected is False: return None
		else: return self.pv[attribute].get()

	def writeValue(self,attribute,value):
		if self._connected is False: return None
		else: 
			if attribute == 'TWV':
				self.pv[attribute].put(value)
			else:
				while self.pv['DMOV'] == 1:
					pass
				self.pv[attribute].put(value)

	def read(self):
		# Straight up reading where the motor is.
		if self._connected is False: return np.inf 
		else: return self.pv['RBV'].get()

	def write(self,value,mode='absolute'):
		if self._connected is False: return
		# Straight up telling the motor where to go.
		elif mode=='absolute':
			if self.pv['VAL']: self.pv['VAL'].put(float(value))
		elif mode=='relative':
			if self.pv['TWV']:
				# Place tweak value.
				self.pv['TWV'].put(float(np.absolute(value)))
				if value < 0:
					# Negative direction
					self.pv['TWR'].put(1)
				elif value > 0:
					self.pv['TWF'].put(1)
				else:
					# Do nothing.
					pass
		else:
			print('Failed to write value ',value,' to motor ',self.movement)