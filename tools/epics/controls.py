import epics
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from functools import partial
import numpy as np
import csv
import os 

def importMotorListCSV(file):
	'''
	CSV file must contain the following headers:
	-	Comment
	-	Stage
	-	Movement
	-	Dependencies
	-	Name
	-	PV
	-	Order
	-	Accuracy
	-	CoR	
	Optional Headers:
	-	Notes
	
	CSV File creation:
	-	The file format may be *.csv or *.txt .
	-	The first row should be the headers.
	-	The second row will be removed as an assumed description section for the headers.
	-	Standard delimeter format for the file should be commas. No functionality currently exists for tabs (or others).
	'''

	# Open csv/txt file and read in.
	f = open(os.path.join(os.path.dirname(__file__),file))
	r = csv.DictReader(f)

	# Save as ordered dict.
	theList = []
	for row in r:
		theList.append(row)

	# Remove the first row, assumed description row.
	del theList[0]

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
	'''
	The controls page is a class designed to contain Qt widgets for motors accessible via EPICS.
	-	This class has its own Qt layout that motor controls can be added to/removed from.
	-	You can read in a CSV file of motors available for the facility (in this case, the Australian Synchrotron Imaging and Medical Beamline).
	- 	There are three levels of motor control to choose from: simple, normal and complex.
	-	There is also a patient dictionary that contains the motors to achieve 6DoF for patient movement.
	'''
	def __init__(self,level='simple',parent=None,stages='motorList.csv',detectors='detectorList.txt'):
		self.layout = QtWidgets.QGridLayout()
		parent.setLayout(self.layout)
		# Motor and detector lists.
		self.motorList = importMotorListCSV(stages)
		self.detectorList = importDetectorList(detectors)
		# Make a list of the stages.
		self.stageList = set()
		for motor in self.motorList:
			self.stageList.add(motor['Stage'])
		# Current list of selected motors.
		self.currentList = []
		# Current list of selected motors' widgets.
		self.currentWidgetList = []
		# Level changes from simple, normal to complex modes.
		self.level = level

		# Set amount of columns in grid layout.
		self.columns = 3
		# Set top left aligment for layout.
		self.layout.setAlignment(QtCore.Qt.AlignTop|QtCore.Qt.AlignLeft)

		# Patient controls
		# Default for no control is None.
		# When a control is set, it should be a QEMotor() class.
		self.patient = {}
		self.patient['tx'] = None
		self.patient['ty'] = None
		self.patient['tz'] = None
		self.patient['rx'] = None
		self.patient['ry'] = None
		self.patient['rz'] = None

	def addMotors(self,group,name=None):
		# Search self.motorList and add a motor widget to the page if it exists.
		# If name is specified, add the single motor.
		# If the name is not specified, add the whole group.
		for motor in self.motorList:
			# Search the list.
			if motor['Stage'] == group:
				# Find motors that match the group.
				if name is None:
					# If no name is specified, add the motor.
					self.addMotorWidget(motor)
				elif self.motor['Name'] == name:
					# Else, check that the motor meets the name requirement.
					# Add the motor.
					self.addMotorWidget(motor)
				else:
					# Do Nothing.
					pass

	def addMotorWidget(self,motor,update=False):
		if motor['PV'] == 'None':
			# If no PV is specified, do not create the widget.
			return

		# Create a new motor widget.
		if self.level == 'simple': motorWidget = QEMotorSimple()
		elif self.level == 'normal': motorWidget = QEMotor()
		elif self.level == 'complex': motorWidget = QEMotorComplex()
		# Add motor vars.
		motorWidget._stage = motor['Stage']
		motorWidget._movement = motor['Movement']
		motorWidget._dependentOn = motor['Dependencies']
		motorWidget._name = motor['Name']
		motorWidget._pv = motor['PV']
		motorWidget._order = motor['Order']
		motorWidget._accuracy = motor['Accuracy']
		motorWidget._cor = motor['CoR']
		# Call motor setup function in light of new vars.
		motorWidget.setup()
		# Add motor to layout.
		self.layout.addWidget(motorWidget)
		# Add motor to current list of motors selected.
		if update is False:
			# If we are not updating the existing motors complexity, add it to the current list.
			self.currentList.append(motor)
		# Add motor widget to current list of motor widgets.
		self.currentWidgetList.append(motorWidget)

		# Add motor to patient movement if required.
		if motor['Movement'] in self.patient:
			# Essentially if the motor is 'tx', look for 'tx' in patient and assign it the QEMotor(), tx.
			self.patient[motor['Movement']] = motorWidget

	def setStage(self,group):
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

		# Add group motors.
		self.addMotors(group)

	def setLevel(self,level):
		self.level = level

		# Remove all widgets and re-add them in level required.
		for i in reversed(range(self.layout.count())): 
			self.layout.itemAt(i).widget().setParent(None)
		self.currentWidgetList = []

		# Add back new ones.
		for motor in self.currentList:
			self.addMotorWidget(motor,update=True)

	def setDetector(self,detector):
		pass

	def setReadOnly(self,state):
		'''If read only then disable components of motor widgets that have moving capabilities.'''
		for motorWidget in self.currentWidgetList:
			motorWidget.setReadOnly(state)

class QEMotor(QtWidgets.QWidget):
	''' A simple layout for epics control in Qt5. Based of a QtWidget.'''
	def __init__(self,parent=None):
		QtWidgets.QWidget.__init__(self,parent)

		# Internal vars: these should be reflected in the CSV file that the motors list is kept in, see class controlsPage().
		self._stage = None
		self._name = None
		self._movement = None
		self._dependentOn = None
		self._order = None
		self._cor = None
		self._pv = None
		self._accuracy = None

		# PV vars.
		self.pv = {}
		self.pv['RBV'] = None
		self.pv['VAL'] = None
		self.pv['TWV'] = None
		self.pv['TWR'] = None
		self.pv['TWF'] = None
		self.pv['DMOV'] = None

	def setup(self):
		# Once the information has been loaded into the internal vars, setup the motor widget.
		# Set the ui file.
		fp = os.path.join(os.path.dirname(__file__),"QEMotor.ui")
		uic.loadUi(fp,self)
		# Connect to the PV's.
		self._connectPV()
		self.lblName.setText(self._name)

	def _connectPV(self):
		# Record PV root information and connect to motors.
		self.pvBase = self._pv

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

class QEMotorSimple(QEMotor):
	def __init__(self,parent=None):
		super().__init__()

	def setup(self):
		# Once the information has been loaded into the internal vars, setup the motor widget.
		# Set the ui file.
		fp = os.path.join(os.path.dirname(__file__),"QEMotorSimple.ui")
		uic.loadUi(fp,self)
		# Connect to the PV's.
		self._connectPV()
		self.lblName.setText(self._name)

class QEMotorComplex(QEMotor):
	def __init__(self,parent=None):
		super().__init__()

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
		# self._connectPV()

# Validators
class QEFloatValidator(QtGui.QDoubleValidator):
	def __init__(self):
		super().__init__()
		self.setDecimals(3)
		self.setBottom(0)