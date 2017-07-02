from PyQt5 import QtGui, uic, QtWidgets, QtCore
from epics import PV
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

	def changeLevel(self,level):
		self.level = level

		# Remove all widgets and re-add them in level required.
		for i in reversed(range(self.layout.count())): 
			self.layout.itemAt(i).widget().setParent(None)

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
		pass

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
		self.labelMotorName.setText(motor)

	def connectPV(self):
		pass

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

class QEMotorComplex(QtWidgets.QWidget):
	''' A simple layout for epics control in Qt5. Based of a QtWidget.'''
	def __init__(self,group,motor,pv,parent=None):
		QtWidgets.QWidget.__init__(self,parent)
		fp = os.path.join(os.path.dirname(__file__),"QEMotorComplex.ui")
		uic.loadUi(fp,self)

		# Set text label
		# self.labelMotorName.setText(motor)

	def connectPV(self):
		pass

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





'''
import epics
import time
def onChanges(pvname=None, value=None, char_value=None, **kw):
	print 'PV Changed! ', pvname, char_value, time.ctime()


mypv = epics.PV(pvname)
mypv.add_callback(onChanges)

print 'Now wait for changes'

t0 = time.time()
while time.time() - t0 < 60.0:
	time.sleep(1.e-3)
print 'Done.'
'''


'''
# example of using a connection callback that will be called
# for any change in connection status

import epics
import time
import sys
from  pvnames import motor1

write = sys.stdout.write
def onConnectionChange(pvname=None, conn= None, **kws):
	write('PV connection status changed: %s %s\n' % (pvname,  repr(conn)))
	sys.stdout.flush()

def onValueChange(pvname=None, value=None, host=None, **kws):
	write('PV value changed: %s (%s)  %s\n' % ( pvname, host, repr(value)))
	sys.stdout.flush()
mypv = epics.PV(motor1, 
				connection_callback= onConnectionChange,
				callback= onValueChange)

mypv.get()

write('Now waiting, watching values and connection changes:\n')
t0 = time.time()
while time.time()-t0 < 300:
	time.sleep(0.01)
'''