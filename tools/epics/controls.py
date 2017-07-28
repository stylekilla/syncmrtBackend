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

	def addMotor(self,group,name):
		# Find and add motor to page.
		for motor in self.motorList:
			if (motor['Group'] == group) & (motor['Name'] == name):
				group,name,pv = motor['Group'],motor['Name'],motor['PV']
				if self.level == 'simple': motorWidget = QEMotorSimple(group,name,pv)
				elif self.level == 'normal': motorWidget = QEMotor(group,name,pv)
				elif self.level == 'complex': motorWidget = QEMotorComplex(group,name,pv)
				self.layout.addWidget(motorWidget)
				self.currentList.append(motor)
				self.currentWidgetList.append(motorWidget)

	def addMotorGroup(self,group):
		# Find and add motors to page.
		for motor in self.motorList:
			# print(motor)
			if motor['Group'] == group:
				group,name,pv = motor['Group'],motor['Name'],motor['PV']
				if self.level == 'simple': motorWidget = QEMotorSimple(group,name,pv)
				elif self.level == 'normal': motorWidget = QEMotor(group,name,pv)
				elif self.level == 'complex': motorWidget = QEMotorComplex(group,name,pv)
				self.layout.addWidget(motorWidget)
				self.currentList.append(motor)
				self.currentWidgetList.append(motorWidget)

	def setMotorGroup(self,group):
		# Remove all existing widgets.
		for i in reversed(range(self.layout.count())): 
			self.layout.itemAt(i).widget().setParent(None)
		self.currentWidgetList = []
		self.currentList = []

		# Find and add motors to page.
		for motor in self.motorList:
			# print(motor)
			if motor['Group'] == group:
				group,name,pv = motor['Group'],motor['Name'],motor['PV']
				if self.level == 'simple': motorWidget = QEMotorSimple(group,name,pv)
				elif self.level == 'normal': motorWidget = QEMotor(group,name,pv)
				elif self.level == 'complex': motorWidget = QEMotorComplex(group,name,pv)
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
			group,name,pv = motor['Group'],motor['Name'],motor['PV']
			if self.level == 'simple': 
				motorWidget = QEMotorSimple(group,name,pv)
			elif self.level == 'normal':
				motorWidget = QEMotor(group,name,pv)
			elif self.level == 'complex':
				motorWidget = QEMotorComplex(group,name,pv)
			self.layout.addWidget(motorWidget)
			self.currentWidgetList.append(motorWidget)

	def setDetector(self,detector):
		# self.
		pass

	def setReadOnly(self,state):
		'''If read only then disable components of motor widgets that have moving capabilities.'''
		for motorWidget in self.currentWidgetList:
			motorWidget.setReadOnly(state)


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

# Motors
class QEMotorSimple(QtWidgets.QWidget):
	''' A simple layout for epics control in Qt5. Based of a QtWidget.'''
	def __init__(self,group,motor,pv,parent=None):
		QtWidgets.QWidget.__init__(self,parent)
		fp = os.path.join(os.path.dirname(__file__),"QEMotorSimple.ui")
		uic.loadUi(fp,self)

		# Set text label
		self.name.setText(motor)

		# Record PV root information and connect to motors.
		self.pvBase = pv
		self.pv = {}
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
			# Read Back Value
			self.pv['DMOV'] = epics.PV(self.pvBase+'.DMOV')
		except:
			pass
		try:
			# Value to put to motor
			self.pv['VAL'] = epics.PV(self.pvBase+'.VAL',callback=partial(self.updateValue, attribute='VAL') )
			self.guiVAL.setValidator(QEFloatValidator())
			self.guiVAL.setEnabled(True)
			self.guiVAL.returnPressed.connect(partial(self.writeValue,attribute='VAL'))
		except:
			self.guiVAL.setEnabled(False)
		try:
			# Tweak Value
			self.pv['TWV'] = epics.PV(self.pvBase+'.TWV',callback=partial(self.updateValue, attribute='TWV') )
			self.guiTWV.setValidator(QEFloatValidator())
			self.guiTWV.setEnabled(True)
			self.guiTWV.returnPressed.connect(partial(self.writeValue,attribute='TWV'))
		except:
			self.guiTWV.setEnabled(False)
		try:
			# Tweak Reverse
			self.pv['TWR'] = epics.PV(self.pvBase+'.TWR')
			self.guiTWR.setEnabled(True)
			self.guiTWR.clicked.connect(partial(self.writeValue,attribute='TWR'))
		except:
			self.guiTWR.setEnabled(False)
		try:
			# Tweak Forward
			self.pv['TWF'] = epics.PV(self.pvBase+'.TWF')
			self.guiTWF.setEnabled(True)
			self.guiTWF.clicked.connect(partial(self.writeValue,attribute='TWF'))
		except:
			self.guiTWF.setEnabled(False)

	def updateValue(self,attribute,pvname=None,value=None,**kw):
		'''Callback function for when the motor value updates.'''
		value = str('{0:.4f}'.format(value))

		if attribute == 'RBV':
			self.guiRBV.setText(value)
		elif attribute == 'VAL':
			self.guiVAL.setText(value)
		elif attribute == 'TWV':
			self.guiTWV.setText(value)
		else:
			pass

	def writeValue(self,attribute):
		'''Write a value to a PV.'''
		# If the motor is currently moving, do nothing. Unless it is the TWV, that doesn't matter.
		if attribute == 'TWV':
			# Update tweak value.
			self.pv[attribute].put( 
				float(self.guiTWV.getText())
				)
		elif self.pv['DMOV'].get() == 0:
			# If we are moving, do nothing.
			return
		else:
			if attribute == 'TWF':
				# Update tweak value.
				self.pv[attribute].put(1)			
			elif attribute == 'TWR':
				# Update tweak value.
				self.pv[attribute].put(1)
			elif attribute == 'VAL':
				# Put motor value.
				self.pv[attribute].put( float(self.guiVAL.getText()) )
			else:
				pass

	def setReadOnly(self,state):
		# Set all items to state = True/False
		self.guiVAL.setEnabled(state)
		self.guiTWV.setEnabled(state)
		self.guiTWF.setEnabled(state)
		self.guiTWR.setEnabled(state)

class QEMotor(QEMotorSimple):
	def __init__(self,group,motor,pv,parent=None):
		super().__init__(group,motor,pv,parent)

class QEMotorComplex(QEMotor):
	def __init__(self,group,motor,pv,parent=None):
		super().__init__(group,motor,pv,parent)

# Detectors
class QEDetector(QtWidgets.QWidget):
	def __init__(self,group,motor,pv,parent=None):
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