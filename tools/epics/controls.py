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
	def __init__(self,level='simple',parent=None,fp='motorList.txt'):
		self.layout = QtWidgets.QGridLayout()
		parent.setLayout(self.layout)
		self.motorList = controlsList(fp)
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

	def setReadOnly(self,state):
		'''If read only then disable components of motor widgets that have moving capabilities.'''
		for motorWidget in self.currentWidgetList:
			motorWidget.setReadOnly(state)


def controlsList(file):
	''' CSV files must have three headers, Group Name and PV.'''
	''' CSV comments are made with a hashtag #.'''
	# Open csv/txt file and read in.
	f = open(os.path.join(os.path.dirname(__file__),file))
	r = csv.DictReader(f)

	# Save as ordered dict.
	controls = []
	for row in r:
		if row['Group'][0] != '#':
			controls.append(row)

	return controls


class QEMotor(QtWidgets.QWidget):
	''' A simple layout for epics control in Qt5. Based of a QtWidget.'''
	def __init__(self,group,motor,pv,parent=None):
		QtWidgets.QWidget.__init__(self,parent)
		fp = os.path.join(os.path.dirname(__file__),"QEMotor.ui")
		uic.loadUi(fp,self)

		# Setup validators for inputs.
		self.stepSize.setValidator(QEFloatValidator())
		self.limitLower.setValidator(QEFloatValidator())
		self.limitUpper.setValidator(QEFloatValidator())
		self.currentPosition.setValidator(QEFloatValidator())

		# Connect buttons.
		self.pbStepsizeMuchSmaller.clicked.connect(partial(self.adjustStepSize,0.1))
		self.pbStepsizeSmaller.clicked.connect(partial(self.adjustStepSize,0.5))
		self.pbStepsizeLarger.clicked.connect(partial(self.adjustStepSize,2))
		self.pbStepsizeMuchLarger.clicked.connect(partial(self.adjustStepSize,10))

		# Set text label
		# self.labelMotorName.setText(motor)

	def connectPV(self):
		# Read Back Value
		try:
			self.pvRBV = epics.PV(self.pv+'.RBV')
			self.guiRBV.setEnabled(True)
		except:
			self.guiRBV.setEnabled(False)
		# Value to put to motor
		try:
			self.pvVAL = epics.PV(self.pv+'.VAL')
			self.guiVAL.setEnabled(True)
		except:
			self.guiVAL.setEnabled(False)
		# Tweak Value
		try:
			self.pvTWV = epics.PV(self.pv+'.TWV')
			self.guiTWV.setEnabled(True)
		except:
			self.guiTWV.setEnabled(False)
		# Tweak Reverse/forward
		try:
			self.pvTWR = epics.PV(self.pv+'.TWR')
			self.guiTWR.setEnabled(True)
		except:
			self.guiTWR.setEnabled(False)
		# Tweak Reverse/forward
		try:
			self.pvTWF = epics.PV(self.pv+'.TWF')
			self.guiTWF.setEnabled(True)
		except:
			self.guiTWF.setEnabled(False)

	def motorPosition(self):
		pass

	def adjustStepSize(self,amount):
		value = np.around(float(self.stepSize.text())*amount,decimals=3)
		self.stepSize.setText(str(value))

	def moveStep(self,direction,limit=False):
		if direction == 'forward':
			if limit:
				pass
			else:
				pass
		elif direction == 'backward':
			if limit:
				pass
			else:
				pass

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
			self.pv['RBV'] = epics.PV(self.pvBase+'.RBV',callback=self.updateRBV)
			self.guiRBV.setEnabled(True)
			self.guiRBV.setReadOnly(True)
			self.guiRBV.setText(str(self.pv['RBV'].get()))
			self.guiRBV.setValidator(QEFloatValidator)
			# self.pvRBV.add_callback(self.motorUpdate)
		except:
			self.guiRBV.setEnabled(False)
		try:
			# Value to put to motor
			self.pv['VAL'] = epics.PV(self.pvBase+'.VAL')
			self.guiVAL.setValidator(QEFloatValidator())
			self.guiVAL.setEnabled(True)
			self.guiVAL.returnPressed.connect(partial(self.writeValue,attribute='VAL',value=float(self.guiVAL.text())))
		except:
			self.guiVAL.setEnabled(False)
		try:
			# Tweak Value
			self.pv['TWV'] = epics.PV(self.pvBase+'.TWV')
			self.guiTWV.setValidator(QEFloatValidator())
			self.guiTWV.setEnabled(True)
			self.guiTWV.returnPressed.connect(partial(self.writeValue,attribute='TWV',value=float(self.guiTWV.text())))
		except:
			self.guiTWV.setEnabled(False)
		try:
			# Tweak Reverse/forward
			self.pv['TWR'] = epics.PV(self.pvBase+'.TWR')
			self.guiTWR.setEnabled(True)
			self.guiTWR.clicked.connect(partial(self.writeValue,attribute='TWR',value=1))
		except:
			self.guiTWR.setEnabled(False)
		try:
			# Tweak Reverse/forward
			self.pv['TWF'] = epics.PV(self.pvBase+'.TWF')
			self.guiTWF.setEnabled(True)
			self.guiTWF.clicked.connect(partial(self.writeValue,attribute='TWR',value=1))
		except:
			self.guiTWF.setEnabled(False)

	def updateRBV(self,pvname=None,value=None,**kw):
		'''Callback function for when the motor value updates.'''
		self.guiRBV.setText(str(value))

	def writeValue(self,attribute,value):
		'''Write a value to a PV.'''
		# If the motor is currently moving, do nothing. Unless it is the TWV, that doesn't matter.
		if attribute == 'TWV':
			# Update tweak value.
			self.pv[attribute].put(value)
		elif self.pv['VAL'].status:
			# If we are moving, do nothing.
			return
		else:
			# If no special case is executed, then write the value.
			self.pv[attribute].put(value)

	def setReadOnly(self,state):
		# Set all items to state = True/False
		self.guiVAL.setEnabled(state)
		self.guiTWV.setEnabled(state)
		self.guiTWF.setEnabled(state)
		self.guiTWR.setEnabled(state)

class QEMotorComplex(QtWidgets.QWidget):
	''' A simple layout for epics control in Qt5. Based of a QtWidget.'''
	def __init__(self,group,motor,pv,parent=None):
		QtWidgets.QWidget.__init__(self,parent)
		fp = os.path.join(os.path.dirname(__file__),"QEMotorComplex.ui")
		uic.loadUi(fp,self)

		# Set text label
		# self.labelMotorName.setText(motor)

	def connectPV(self):
		# Read Back Value
		try:
			self.pvRBV = epics.PV(self.pv+'.RBV')
			self.guiRBV.setEnabled(True)
		except:
			self.guiRBV.setEnabled(False)
		# Value to put to motor
		try:
			self.pvVAL = epics.PV(self.pv+'.VAL')
			self.guiVAL.setEnabled(True)
		except:
			self.guiVAL.setEnabled(False)
		# Tweak Value
		try:
			self.pvTWV = epics.PV(self.pv+'.TWV')
			self.guiTWV.setEnabled(True)
		except:
			self.guiTWV.setEnabled(False)
		# Tweak Reverse/forward
		try:
			self.pvTWR = epics.PV(self.pv+'.TWR')
			self.guiTWR.setEnabled(True)
		except:
			self.guiTWR.setEnabled(False)
		# Tweak Reverse/forward
		try:
			self.pvTWF = epics.PV(self.pv+'.TWF')
			self.guiTWF.setEnabled(True)
		except:
			self.guiTWF.setEnabled(False)

	def motorPosition(self):
		pass

	def moveStep(self,direction,limit=False):
		if direction == 'forward':
			if limit:
				pass
			else:
				pass
		elif direction == 'backward':
			if limit:
				pass
			else:
				pass


class QEFloatValidator(QtGui.QDoubleValidator):
	def __init__(self):
		super().__init__()
		self.setDecimals(3)
		self.setBottom(0)