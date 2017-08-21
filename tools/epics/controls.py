import epics
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from functools import partial
import numpy as np
import csv
import os 

'''
class controlsPage:
	- Designed to create a layout in a parent widget that can house the widgets for epics controls.
	- __init__(parentWidget,filepath to csv file containing motors)
		- CSV file must contain headers: Group, Name, PV
			- comments may be presented with a '#'
			- may have blank lines
			- all fields must not be left blank
	- addMotor(group,name): can specify a single motor to add from the list
	- addMotorGroup(group): can specify a whole group of motors to add from the list
'''

def importMotorList(file):
	''' CSV files must have three headers, Group Name and PV.'''
	''' CSV comments are made with a hashtag #.'''
	# Open csv/txt file and read in.
	f = open(os.path.join(os.path.dirname(__file__),file))
	r = csv.DictReader(f)

	# Save as ordered dict.
	theList = []
	for row in r:
		if row['Group'][0] != '#':
			theList.append(row)

	return theList

def importDetectorList(file):
	''' CSV files must have three headers, Group Name and PV.'''
	''' CSV comments are made with a hashtag #.'''
	# Open csv/txt file and read in.
	f = open(os.path.join(os.path.dirname(__file__),file))
	r = csv.DictReader(f)

	# Save as ordered dict.
	theList = []
	for row in r:
		if row['Name'][0] != '#':
			theList.append(row)

	return theList

class controlsPage:
	def __init__(self,level='simple',parent=None,stages='motorList.txt',detectors='detectorList.txt'):
		self.layout = QtWidgets.QGridLayout()
		parent.setLayout(self.layout)
		self.motorList = importMotorList(stages)
		self.detectorList = importDetectorList(detectors)
		self.currentList = []
		self.currentWidgetList = []
		# Level changes from simple, normal to complex modes.
		self.level = level

		# Set amount of columns in grid layout.
		self.columns = 3
		# Set top left aligment for layout.
		self.layout.setAlignment(QtCore.Qt.AlignTop|QtCore.Qt.AlignLeft)

		# Patient controls
		self.patient = {}
		self.patient['tx'] = None
		self.patient['ty'] = None
		self.patient['tz'] = None
		self.patient['rx'] = None
		self.patient['ry'] = None
		self.patient['rz'] = None

	def addMotor(self,group,name):
		# Find and add motor to page.
		for motor in self.motorList:
			if (motor['Group'] == group) & (motor['Name'] == name):
				group,movement,dependentOn,name,pv = motor['Group'],motor['Movement'],motor['dependentOn'],motor['Name'],motor['PV']
				if self.level == 'simple': motorWidget = QEMotorSimple(group,movement,dependentOn,name,pv)
				elif self.level == 'normal': motorWidget = QEMotor(group,movement,dependentOn,name,pv)
				elif self.level == 'complex': motorWidget = QEMotorComplex(group,movement,dependentOn,name,pv)
				if motor['Movement'] in self.patient: self.patient[motor['Movement']] = motorWidget
				self.layout.addWidget(motorWidget)
				self.currentList.append(motor)
				self.currentWidgetList.append(motorWidget)

	def addMotorGroup(self,group):
		# Find and add motors to page.
		for motor in self.motorList:
			# print(motor)
			if motor['Group'] == group:
				group,movement,dependentOn,name,pv = motor['Group'],motor['Movement'],motor['dependentOn'],motor['Name'],motor['PV']
				if self.level == 'simple': motorWidget = QEMotorSimple(group,movement,dependentOn,name,pv)
				elif self.level == 'normal': motorWidget = QEMotor(group,movement,dependentOn,name,pv)
				elif self.level == 'complex': motorWidget = QEMotorComplex(group,movement,dependentOn,name,pv)
				if motor['Movement'] in self.patient: self.patient[motor['Movement']] = motorWidget
				self.layout.addWidget(motorWidget)
				self.currentList.append(motor)
				self.currentWidgetList.append(motorWidget)

	def setMotorGroup(self,group):
		# Remove all existing widgets.
		for i in reversed(range(self.layout.count())): 
			self.layout.itemAt(i).widget().setParent(None)
		self.currentWidgetList = []
		self.currentList = []

		# Reset linked motors to None.
		self.patient['tx'] = None
		self.patient['ty'] = None
		self.patient['tz'] = None
		self.patient['rx'] = None
		self.patient['ry'] = None
		self.patient['rz'] = None

		# Find and add motors to page.
		for motor in self.motorList:
			# print(motor)
			if motor['Group'] == group:
				group,movement,dependentOn,name,pv = motor['Group'],motor['Movement'],motor['dependentOn'],motor['Name'],motor['PV']
				if self.level == 'simple': motorWidget = QEMotorSimple(group,movement,dependentOn,name,pv)
				elif self.level == 'normal': motorWidget = QEMotor(group,movement,dependentOn,name,pv)
				elif self.level == 'complex': motorWidget = QEMotorComplex(group,movement,dependentOn,name,pv)

				if motor['Movement'] in self.patient: 
					self.patient[motor['Movement']] = motorWidget
				else: 
					pass

				self.layout.addWidget(motorWidget)
				self.currentList.append(motor)
				self.currentWidgetList.append(motorWidget)

	def setLevel(self,level):
		self.level = level

		# Remove all widgets and re-add them in level required.
		for i in reversed(range(self.layout.count())): 
			self.layout.itemAt(i).widget().setParent(None)
		self.currentWidgetList = []

		# Add back new ones.
		for motor in self.currentList:
			group,movement,dependentOn,name,pv = motor['Group'],motor['Movement'],motor['dependentOn'],motor['Name'],motor['PV']
			if self.level == 'simple': 
				motorWidget = QEMotorSimple(group,movement,dependentOn,name,pv)
			elif self.level == 'normal':
				motorWidget = QEMotor(group,movement,dependentOn,name,pv)
			elif self.level == 'complex':
				motorWidget = QEMotorComplex(group,movement,dependentOn,name,pv)
			self.layout.addWidget(motorWidget)
			self.currentWidgetList.append(motorWidget)

	def setDetector(self,detector):
		pass

	def setReadOnly(self,state):
		'''If read only then disable components of motor widgets that have moving capabilities.'''
		for motorWidget in self.currentWidgetList:
			motorWidget.setReadOnly(state)

# Motors
class QEMotorSimple(QtWidgets.QWidget):
	''' A simple layout for epics control in Qt5. Based of a QtWidget.'''
	def __init__(self,group,movement,dependentOn,name,pv,parent=None):
		QtWidgets.QWidget.__init__(self,parent)
		fp = os.path.join(os.path.dirname(__file__),"QEMotorSimple.ui")
		uic.loadUi(fp,self)

		# Set text label
		self.name.setText(name)

		# Record PV root information and connect to motors.
		self.pvBase = pv
		self.pv = {}
		self.pv['RBV'] = None
		self.pv['VAL'] = None
		self.pv['TWV'] = None
		self.pv['TWR'] = None
		self.pv['TWF'] = None
		self.pv['DMOV'] = None

		# Is the motor affected by any other motor?
		self.movement = movement
		self.dependentOn = dependentOn

		# Connect to the PV's.
		self.connectPV()

	def connectPV(self):
		try:
			# Read Back Value
			self.pv['RBV'] = epics.PV(self.pvBase+'.RBV',callback=partial(self.updateValue, attribute='RBV') )
			self.guiRBV.setEnabled(True)
			self.guiRBV.setReadOnly(True)
			self.guiRBV.setText(str(self.pv['RBV'].get()))
			self.guiRBV.setValidator(QEFloatValidator)
		except:
			self.guiRBV.setEnabled(False)
		try:
			# Is motor moving?
			self.pv['DMOV'] = epics.PV(self.pvBase+'.DMOV')
		except:
			pass
		try:
			# Value to put to motor
			self.pv['VAL'] = epics.PV(self.pvBase+'.VAL',callback=partial(self.updateValue, attribute='VAL') )
			self.guiVAL.setValidator(QEFloatValidator())
			self.guiVAL.setEnabled(True)
			self.guiVAL.returnPressed.connect(partial(self.writeValue,attribute='VAL',value=float(self.guiVAL.getText())))
		except:
			self.guiVAL.setEnabled(False)
		try:
			# Tweak Value
			self.pv['TWV'] = epics.PV(self.pvBase+'.TWV',callback=partial(self.updateValue, attribute='TWV') )
			self.guiTWV.setValidator(QEFloatValidator())
			self.guiTWV.setEnabled(True)
			self.guiTWV.returnPressed.connect(partial(self.writeValue,attribute='TWV',value=float(self.guiTWV.getText())))
		except:
			self.guiTWV.setEnabled(False)
		try:
			# Tweak Reverse
			self.pv['TWR'] = epics.PV(self.pvBase+'.TWR')
			self.guiTWR.setEnabled(True)
			self.guiTWR.clicked.connect(partial(self.writeValue,attribute='TWR',value=1))
		except:
			self.guiTWR.setEnabled(False)
		try:
			# Tweak Forward
			self.pv['TWF'] = epics.PV(self.pvBase+'.TWF')
			self.guiTWF.setEnabled(True)
			self.guiTWF.clicked.connect(partial(self.writeValue,attribute='TWF',value=1))
		except:
			self.guiTWF.setEnabled(False)

	def updateValue(self,attribute,pvname=None,value=None,**kw):
		'''Callback function for when the motor value updates.'''
		value = str('{0:.4f}'.format(value))

		if attribute == 'RBV':
			# Not set by user. Set by PV readback.
			self.guiRBV.setText(value)
		elif attribute == 'VAL':
			# Set by user in gui and by PV readback.
			self.guiVAL.setText(value)
		elif attribute == 'TWV':
			# Set by user in gui and by PV readback.
			self.guiTWV.setText(value)
		else:
			pass

	def readValue(self,attribute):
		if self.pv[attribute] is None:
			return None
		else:
			return self.pv[attribute].get()

	def writeValue(self,attribute,value=None):
		'''Write a value to a PV.'''
		# Check to see if a pv is connected.
		if self.pv[attribute] is None:
			print('PV',self.pv[attribute],' not connected, unable to write ',value)
			return
		else:
			# Continue on.
			pass

		# If the motor is currently moving, do nothing, unless it's TWV, then it doesn't matter.
		if attribute == 'TWV':
			# Update tweak value.
			self.pv[attribute].put( 
				float(self.guiTWV.getText())
				)
		elif self.pv['DMOV'].get() == 1:
			# If we are moving, do nothing.
			return
		else:
			self.pv[attribute].put(value)

	def read(self):
		# Straight up reading where the motor is.
		if self.pv['RBV'] is None:
			return np.inf
		else:
			return self.pv['RBV'].get()

	def write(self,value,mode='absolute'):
		# Straight up telling the motor where to go.
		if mode=='absolute':
			if self.pv['VAL']:
				self.pv['VAL'].put(float(value))

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

	def setReadOnly(self,state):
		# Set all items to state = True/False
		self.guiVAL.setEnabled(state)
		self.guiTWV.setEnabled(state)
		self.guiTWF.setEnabled(state)
		self.guiTWR.setEnabled(state)

class QEMotor(QEMotorSimple):
	def __init__(self,group,movement,dependentOn,name,pv,parent=None):
		super().__init__(group,movement,dependentOn,name,pv)

class QEMotorComplex(QEMotor):
	def __init__(self,group,movement,dependentOn,name,pv,parent=None):
		super().__init__(group,movement,dependentOn,name,pv)

# Detectors
class QEDetector(QtWidgets.QWidget):
	def __init__(self,name,pv,parent=None):
		QtWidgets.QWidget.__init__(self,parent)
		# fp = os.path.join(os.path.dirname(__file__),"QEDetector.ui")
		# uic.loadUi(fp,self)

		# # Set text label
		# self.name.setText(motor)

		# # Record PV root information and connect to motors.
		# self.pvBase = pv
		# self.pv = {}
		# self.connectPV()

# Validators
class QEFloatValidator(QtGui.QDoubleValidator):
	def __init__(self):
		super().__init__()
		self.setDecimals(3)
		self.setBottom(0)