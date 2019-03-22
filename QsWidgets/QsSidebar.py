from PyQt5 import QtWidgets, QtGui, QtCore

class QAlignment(QtWidgets.QWidget):
	def __init__(self):
		super().__init__()
		self.widget = {}
		self.layout = QtWidgets.QVBoxLayout()

		# Group 1: Markers
		markerGroup = QtWidgets.QGroupBox()
		markerGroup.setTitle('Marker Options')
		label1 = QtWidgets.QLabel('No. of Markers:')
		self.widget['maxMarkers'] = QtWidgets.QSpinBox()
		self.widget['anatomical'] = QtWidgets.QRadioButton('Anatomical')
		self.widget['fiducial'] = QtWidgets.QRadioButton('Fiducial')
		self.widget['optimise'] = QtWidgets.QCheckBox('Optimise')
		label2 = QtWidgets.QLabel('Marker Size (mm):')
		self.widget['markerSize'] = QtWidgets.QDoubleSpinBox()
		label3 = QtWidgets.QLabel('Threshold (%):')
		self.widget['threshold'] = QtWidgets.QDoubleSpinBox()
		# Layout
		markerGroupLayout = QtWidgets.QFormLayout()
		markerGroupLayout.addRow(label1,self.widget['maxMarkers'])
		markerGroupLayout.addRow(self.widget['anatomical'])
		markerGroupLayout.addRow(self.widget['fiducial'])
		markerGroupLayout.addRow(self.widget['optimise'])
		markerGroupLayout.addRow(label2,self.widget['markerSize'])
		markerGroupLayout.addRow(label3,self.widget['threshold'])
		markerGroup.setLayout(markerGroupLayout)
		self.layout.addWidget(markerGroup)
		# Default Positions
		self.widget['optimise'].setEnabled(False)
		self.widget['anatomical'].setChecked(True)
		self.widget['markerSize'].setEnabled(False)
		self.widget['markerSize'].setRange(1,5)
		self.widget['markerSize'].setSingleStep(0.25)
		self.widget['markerSize'].setValue(2.00)
		self.widget['maxMarkers'].setMinimum(1)
		self.widget['threshold'].setEnabled(False)
		self.widget['threshold'].setRange(0,50)
		self.widget['threshold'].setValue(3)
		self.widget['threshold'].setSingleStep(0.5)
		# Signals and Slots
		self.widget['anatomical'].toggled.connect(self.markerMode)
		self.widget['fiducial'].toggled.connect(self.markerMode)
		self.widget['optimise'].toggled.connect(self.markerMode)

		# Group 2: Checklist
		alignGroup = QtWidgets.QGroupBox()
		alignGroup.setTitle('Patient Alignment')
		self.widget['calcAlignment'] = QtWidgets.QPushButton('Calculate')
		self.widget['doAlignment'] = QtWidgets.QPushButton('Align')
		# Layout
		alignGroupLayout = QtWidgets.QFormLayout()
		alignGroupLayout.addRow(self.widget['calcAlignment'],self.widget['doAlignment'])
		alignGroup.setLayout(alignGroupLayout)
		self.layout.addWidget(alignGroup)
		# Defaults
		# self.widget['doAlignment'].setEnabled(False)
		# Signals and Slots

		# Group 3: Checklist
		checklistGroup = QtWidgets.QGroupBox()
		checklistGroup.setTitle('Checklist')
		self.widget['checkSetup'] = QtWidgets.QLabel('Alignment Setup')
		self.widget['checkXray'] = QtWidgets.QLabel('X-ray')
		self.widget['checkDicom'] = QtWidgets.QLabel('Dicom Image')
		self.widget['checkRTP'] = QtWidgets.QLabel('Treatment Plan')
		# self.widget['check'] = QtWidgets.QPushButton('Check')
		# self.widget['align'] = QtWidgets.QPushButton('Align')
		# Layout
		checklistGroupLayout = QtWidgets.QFormLayout()
		checklistGroupLayout.addRow(self.widget['checkSetup'])
		checklistGroupLayout.addRow(self.widget['checkXray'])
		checklistGroupLayout.addRow(self.widget['checkDicom'])
		checklistGroupLayout.addRow(self.widget['checkRTP'])
		# checklistGroupLayout.addRow(self.widget['check'],self.widget['align'])
		checklistGroup.setLayout(checklistGroupLayout)
		self.layout.addWidget(checklistGroup)
		# Defaults
		# Signals and Slots

		# Finish page.
		self.layout.addStretch(1)
		self.updateLayout()

	def updateLayout(self):
		self.setLayout(self.layout)

	def markerMode(self):
		'''If fiducial markers are chosen then enable optimisation checkbox and sizing.'''
		# Enabling/toggling optimise.
		if self.widget['fiducial'].isChecked():
			self.widget['optimise'].setEnabled(True)
		else:
			self.widget['optimise'].setEnabled(False)
			self.widget['optimise'].setChecked(False)
			self.widget['markerSize'].setEnabled(False)
			self.widget['threshold'].setEnabled(False)

		# Enabling/toggling markerSize.
		if self.widget['optimise'].isChecked():
			self.widget['markerSize'].setEnabled(True)
			self.widget['threshold'].setEnabled(True)
		else:
			self.widget['markerSize'].setEnabled(False)
			self.widget['threshold'].setEnabled(False)

	def delete(self):
		for key, val in self.widget:
			del key
		del self.layout

class QTreatment(QtWidgets.QWidget):
	def __init__(self):
		super().__init__()
		self.widget = {}
		self.layout = QtWidgets.QVBoxLayout()

		# Group 1: Treatment Settings
		settingsGroup = QtWidgets.QGroupBox()
		settingsGroup.setTitle('Description')
		label1 = QtWidgets.QLabel('Number of beams: ')
		self.widget['quantity'] = QtWidgets.QLabel()
		# Layout
		settingsGroupLayout = QtWidgets.QFormLayout()
		settingsGroupLayout.addRow(label1,self.widget['quantity'])
		settingsGroup.setLayout(settingsGroupLayout)
		self.layout.addWidget(settingsGroup)
		# Defaults
		self.widget['quantity'].setText(str(0))
		# Signals and Slots

		# Group 2: Deliver Treatment
		# Dict for beam plan group widgets.
		self.widget['beam'] = {}
		group = QtWidgets.QGroupBox()
		group.setTitle('Deliver Treatment')
		# Empty Layout
		self.widget['deliveryGroup'] = QtWidgets.QFormLayout()
		self.widget['noTreatment'] = QtWidgets.QLabel('No Treatment Plan loaded.')
		self.widget['deliveryGroup'].addRow(self.widget['noTreatment'])
		group.setLayout(self.widget['deliveryGroup'])
		self.layout.addWidget(group)
		# Defaults
		# Signals and Slots

		# Finish page.
		self.layout.addStretch(1)
		self.updateLayout()

	def updateLayout(self):
		self.setLayout(self.layout)


	def populateTreatments(self):
		'''Once treatment plan is loaded, add the treatments to the workflow.'''
		self.widget['noTreatment'].deleteLater()
		del self.widget['noTreatment']

		for i in range(int(self.widget['quantity'].text())):	
			self.widget['beam'][i] = {}
			label = QtWidgets.QLabel(str('Beam %i'%(i+1)))
			self.widget['beam'][i]['calculate'] = QtWidgets.QPushButton('Calculate')
			self.widget['beam'][i]['align'] = QtWidgets.QPushButton('Align')
			# self.widget['beam'][i]['hline'] = QHLine()
			self.widget['beam'][i]['interlock'] = QtWidgets.QCheckBox('Interlock')
			self.widget['beam'][i]['deliver'] = QtWidgets.QPushButton('Deliver')
			# Layout
			self.widget['deliveryGroup'].addRow(label)
			self.widget['deliveryGroup'].addRow(self.widget['beam'][i]['calculate'],self.widget['beam'][i]['align'])
			self.widget['deliveryGroup'].addRow(QHLine())
			self.widget['deliveryGroup'].addRow(self.widget['beam'][i]['interlock'],self.widget['beam'][i]['deliver'])
			# Defaults
			self.widget['beam'][i]['alignmentComplete'] = False
			self.widget['beam'][i]['interlock'].setChecked(True)
			self.widget['beam'][i]['interlock'].setEnabled(False)
			self.widget['beam'][i]['deliver'].setEnabled(False)
			# Signals and Slots
			self.widget['beam'][i]['interlock'].stateChanged.connect(partial(self.treatmentInterlock,i))

	def treatmentInterlock(self,index):
		'''Treatment interlock stops treatment from occuring. Requires alignment to be done first.'''
		# Enable interlock button.
		if self.widget['beam'][index]['alignmentComplete'] == True:
			self.widget['beam'][index]['interlock'].setEnabled(True)

		# Enable widget delivery button.
		if self.widget['beam'][index]['interlock'].isChecked():
			self.widget['beam'][index]['deliver'].setEnabled(False)
		else:
			self.widget['beam'][index]['deliver'].setEnabled(True)

	def delete(self):
		for key, val in self.widget:
			del key
		del self.layout

class QSettings(QtWidgets.QWidget):
	modeChanged = QtCore.pyqtSignal('QString')
	stageChanged = QtCore.pyqtSignal('QString')
	detectorChanged = QtCore.pyqtSignal('QString')

	def __init__(self):
		super().__init__()
		self.controls = {}
		self.hardware = {}
		self.layout = QtWidgets.QVBoxLayout()

		# Group 1: Controls Level
		controlsGroup = QtWidgets.QGroupBox()
		controlsGroup.setTitle('Control Complexity')
		self.controls['rbSimple'] = QtWidgets.QRadioButton('Simple')
		self.controls['rbNormal'] = QtWidgets.QRadioButton('Normal')
		self.controls['rbComplex'] = QtWidgets.QRadioButton('Complex')
		self.controls['cbReadOnly'] = QtWidgets.QCheckBox('Read Only')
		self.controls['complexity'] = 'simple'
		# Layout
		controlsGroupLayout = QtWidgets.QVBoxLayout()
		controlsGroupLayout.addWidget(self.controls['rbSimple'])
		controlsGroupLayout.addWidget(self.controls['rbNormal'])
		controlsGroupLayout.addWidget(self.controls['rbComplex'])
		controlsGroupLayout.addWidget(self.controls['cbReadOnly'])
		controlsGroup.setLayout(controlsGroupLayout)

		# Group 2: Hardware
		hardwareGroup = QtWidgets.QGroupBox()
		hardwareGroup.setTitle('Hardware Configuration')
		detectorLabel = QtWidgets.QLabel('Stage')
		self.hardware['stage'] = QtWidgets.QComboBox()
		stageLabel = QtWidgets.QLabel('Detector')
		self.hardware['detector'] = QtWidgets.QComboBox()
		# Layout
		hardwareGroupLayout = QtWidgets.QVBoxLayout()
		hardwareGroupLayout.addWidget(detectorLabel)
		hardwareGroupLayout.addWidget(self.hardware['stage'])
		hardwareGroupLayout.addWidget(stageLabel)
		hardwareGroupLayout.addWidget(self.hardware['detector'])
		hardwareGroup.setLayout(hardwareGroupLayout)

		# Defaults
		self.controls['rbSimple'].setChecked(True)
		self.controls['cbReadOnly'].setChecked(True)
		# Signals and Slots
		self.controls['rbSimple'].clicked.connect(self.controlsMode)
		self.controls['rbNormal'].clicked.connect(self.controlsMode)
		self.controls['rbComplex'].clicked.connect(self.controlsMode)
		self.hardware['stage'].currentIndexChanged.connect(self.stageChange)
		self.hardware['detector'].currentIndexChanged.connect(self.detectorChange)
		# Add Sections
		self.layout.addWidget(controlsGroup)
		self.layout.addWidget(hardwareGroup)
		# Finish page.
		self.layout.addStretch(1)
		self.setLayout(self.layout)

	def controlsMode(self):
		''' Set complexity of controls. '''
		if self.controls['rbSimple'].isChecked():
			self.controls['complexity'] = 'simple'
		elif self.controls['rbNormal'].isChecked():
			self.controls['complexity'] = 'normal'
		elif self.controls['rbComplex'].isChecked():
			self.controls['complexity'] = 'complex'

		# Emit signal to say state has changed.
		self.modeChanged.emit(self.controls['complexity'])

	def loadStages(self,stageList):
		# stageList should be a list of strings of the stages available to choose from.
		self.hardware['motorsList'] = stageList

		# For each item in the list, add it to the drop down list.
		for item in self.hardware['motorsList']:
			self.hardware['stage'].addItem(item)

		# Sort the model alphanumerically.
		self.hardware['stage'].model().sort(0)

	def stageChange(self):
		self.stageChanged.emit(self.hardware['stage'].currentText())

	def loadDetectors(self,importList):
		'''Expects a dict of csv values.'''
		self.hardware['detectorList'] = set()
		for detector in importList:
			self.hardware['detectorList'].add(detector['Name'])

		for item in self.hardware['detectorList']:
			self.hardware['detector'].addItem(item)

		self.hardware['detector'].model().sort(0)

	def detectorChange(self):
		self.detectorChanged.emit(self.hardware['detector'].currentText())

	def delete(self):
		for key, val in self.widget:
			del key
		del self.layout

class QXrayProperties(QtWidgets.QWidget):
	def __init__(self,parent=None):
		super().__init__()
		# self.parent = parent
		self.widget = {}
		self.layout = QtWidgets.QVBoxLayout()

		# # Group 1: Editable Isocenter
		# editIsocenter = QtWidgets.QGroupBox()
		# editIsocenter.setTitle('Edit Treatment Isocenter')
		# label1 = QtWidgets.QLabel('Isocenter (mm)')
		# label2 = QtWidgets.QLabel('x: ')
		# self.widget['alignIsocX'] = QtWidgets.QLineEdit()
		# label3 = QtWidgets.QLabel('y: ')
		# self.widget['alignIsocY'] = QtWidgets.QLineEdit()
		# # Layout
		# editIsocenterLayout = QtWidgets.QFormLayout()
		# editIsocenterLayout.addRow(label1)
		# editIsocenterLayout.addRow(label2,self.widget['alignIsocX'])
		# editIsocenterLayout.addRow(label3,self.widget['alignIsocY'])
		# # Defaults
		# validator = QtGui.QDoubleValidator()
		# validator.setBottom(0)
		# validator.setDecimals(4)
		# self.widget['alignIsocX'].setValidator(validator)
		# self.widget['alignIsocY'].setValidator(validator)
		# # Signals and Slots
		# # Group inclusion to page
		# editIsocenter.setLayout(editIsocenterLayout)
		# self.layout.addWidget(editIsocenter)

		# Group 2: Overlays.
		overlayGroup = QtWidgets.QGroupBox()
		overlayGroup.setTitle('Plot Overlays')
		self.widget['cbBeamIsoc'] = QtWidgets.QCheckBox('Beam Isocenter')
		self.widget['cbPatIsoc'] = QtWidgets.QCheckBox('Patient Isocenter')
		self.widget['cbCentroid'] = QtWidgets.QCheckBox('Centroid Position')
		# Layout
		overlayGroupLayout = QtWidgets.QVBoxLayout()
		overlayGroupLayout.addWidget(self.widget['cbBeamIsoc'])
		overlayGroupLayout.addWidget(self.widget['cbPatIsoc'])
		overlayGroupLayout.addWidget(self.widget['cbCentroid'])
		# Defaults
		# Signals and Slots
		# Group inclusion to page
		overlayGroup.setLayout(overlayGroupLayout)
		self.layout.addWidget(overlayGroup)

		# Group 3: Windowing.
		self.window = {}
		windowGroup = QtWidgets.QGroupBox()
		windowGroup.setTitle('X-ray Windowing')
		self.window['layout'] = QtWidgets.QVBoxLayout()
		# Add two widgets to layout.
		# self.window['window'] = [QtWidgets.QWidget(),QtWidgets.QWidget()]
		# self.window['window'] = QtWidgets.QWidget()
		# Layouts for widgets.
		# self.window['layout'].addWidget(self.window['window'][0])
		# self.window['layout'].addWidget(self.window['window'][1])
		# self.window['histogram'] = QtWidgets.QWidget()
		# self.window['histogram'].setLayout(QtWidgets.QVBoxLayout())
		# self.window['histogram'] = [None,None]
		# self.window['layouts'] = [QtWidgets.QFormLayout(),QtWidgets.QFormLayout()]
		# self.window['window1'].setLayout(self.window['layouts'][0])
		# self.window['window2'].setLayout(self.window['layouts'][1])
		# Set the layout of group.
		windowGroup.setLayout(self.window['layout'])
		# Add group to sidebar layout.
		self.layout.addWidget(windowGroup)

		# Finish page.
		# spacer = QtWidgets.QSpacerItem(0,0)
		# self.layout.addSpacerItem(spacer)
		self.layout.addStretch(1)
		self.setLayout(self.layout)

	def addPlotHistogramWindow(self,widget):
		# These are new ones each time. Remove old wdigets.
		layout = self.window['layout'].layout()
		for i in range(layout.count()):
			layout.removeItem(i)
		# New widgets.
		for i in range(len(widget)):
			layout.addWidget(widget[i])

	# def plotSettings(self,plot):
		# Add histogram and sliders to widget for plot control.
		# self.window['histogram'] = widgets.window(windowGroup,)

	# def addWindows(self):
	# 	'''Add or remove windowing fields as required.'''
	# 	difference = int(self.window['numWindows'].value() - len(self.window['window'])/2)

	# 	# If number greater than, then add windows.
	# 	if difference > 0:
	# 		length = len(self.window['window'])
	# 		for i in range(difference):
	# 			# Add to dict, add to layout.
	# 			self.window['window'][length+i*2] = QXraySpinBox()
	# 			self.window['window'][length+i*2+1] = QXraySpinBox()
	# 			self.window['window'][length+i*2+1].setValue(10000)
	# 			self.window['layout'].insertRow(self.window['layout'].rowCount()-1,
	# 				self.window['window'][length+i],self.window['window'][length+i*2+1])

	# 	# If number less than, remove windows.
	# 	if difference < 0:
	# 		length = len(self.window['window'])
	# 		for i in range(abs(difference)):
	# 			# Remove from layout, remove from dict.
	# 			self.window['window'][length-i*2-1].deleteLater()
	# 			self.window['window'][length-i*2-2].deleteLater()
	# 			del self.window['window'][length-i*2-1]
	# 			del self.window['window'][length-i*2-2]

	# def getWindows(self):
	# 	'''Get window values as list of lists. Need scale slope and intercept.'''
	# 	windows = []

	# 	for i in range(int(len(self.window['window'])/2)):
	# 		window = [self.window['window'][i*2].value(),self.window['window'][i*2+1].value()]
	# 		windows.append(window)

	# 	return windows

class QCtProperties(QtWidgets.QWidget):
	# Qt signals.
	isocenterChanged = QtCore.pyqtSignal(float,float,float)

	def __init__(self):
		# Init QObject class.
		super().__init__()
		# Continue with sub-class initialisation.
		self.group = {}
		self.widget = {}
		self.layout = QtWidgets.QVBoxLayout()

		# Group 1: Overlays.
		overlayGroup = QtWidgets.QGroupBox()
		overlayGroup.setTitle('Plot Overlays')
		self.widget['cbPatIsoc'] = QtWidgets.QCheckBox('Patient Isocenter')
		self.widget['cbCentroid'] = QtWidgets.QCheckBox('Centroid Position')
		# Layout
		overlayGroupLayout = QtWidgets.QVBoxLayout()
		overlayGroupLayout.addWidget(self.widget['cbPatIsoc'])
		overlayGroupLayout.addWidget(self.widget['cbCentroid'])
		# Defaults
		# Signals and Slots
		# Group inclusion to page
		overlayGroup.setLayout(overlayGroupLayout)
		self.layout.addWidget(overlayGroup)

		# Group 2: Editable Isocenter
		# self.group['editIsocenter'] = editIsocenter = QtWidgets.QGroupBox()
		self.group['editIsocenter'] = QtWidgets.QGroupBox()
		self.group['editIsocenter'].setTitle('Edit Treatment Isocenter')
		label1 = QtWidgets.QLabel('Isocenter (mm)')
		label2 = QtWidgets.QLabel('x: ')
		self.widget['isocX'] = QtWidgets.QLineEdit()
		label3 = QtWidgets.QLabel('y: ')
		self.widget['isocY'] = QtWidgets.QLineEdit()
		label4 = QtWidgets.QLabel('z: ')
		self.widget['isocZ'] = QtWidgets.QLineEdit()
		# Layout
		editIsocenterLayout = QtWidgets.QFormLayout()
		editIsocenterLayout.addRow(label1)
		editIsocenterLayout.addRow(label2,self.widget['isocX'])
		editIsocenterLayout.addRow(label3,self.widget['isocY'])
		editIsocenterLayout.addRow(label4,self.widget['isocZ'])
		# Defaults
		self.group['editIsocenter'].setEnabled(False)
		doubleValidator = QtGui.QDoubleValidator()
		# doubleValidator.setBottom(0)
		doubleValidator.setDecimals(3)
		self.widget['isocX'].setText('0')
		self.widget['isocY'].setText('0')
		self.widget['isocZ'].setText('0')
		self.widget['isocX'].setValidator(doubleValidator)
		self.widget['isocY'].setValidator(doubleValidator)
		self.widget['isocZ'].setValidator(doubleValidator)
		# Signals and Slots
		self.widget['isocX'].returnPressed.connect(self.updateIsocenter)
		self.widget['isocY'].returnPressed.connect(self.updateIsocenter)
		self.widget['isocZ'].returnPressed.connect(self.updateIsocenter)
		# Group inclusion to page
		self.group['editIsocenter'].setLayout(editIsocenterLayout)
		self.layout.addWidget(self.group['editIsocenter'])

		# Group 3: Windowing.
		self.window = {}
		windowGroup = QtWidgets.QGroupBox()
		windowGroup.setTitle('CT Windowing')
		self.window['layout'] = QtWidgets.QVBoxLayout()
		# Add two widgets to layout.
		self.window['window'] = [QtWidgets.QWidget(),QtWidgets.QWidget()]
		# Layouts for widgets.
		self.window['layout'].addWidget(self.window['window'][0])
		self.window['layout'].addWidget(self.window['window'][1])
		self.window['histogram'] = [None,None]
		# Set the layout of group.
		windowGroup.setLayout(self.window['layout'])
		# Add group to sidebar layout.
		self.layout.addWidget(windowGroup)

		# Finish page.
		self.layout.addStretch(1)
		self.setLayout(self.layout)

	def addPlotWindow(self,plot,index):
		self.window['histogram'][index] = widgets.mpl.window(self.window['window'][index],plot,advanced=True)

	def updateIsocenter(self):
		# Get all three coordinates.
		x = float( self.widget['isocX'].text() )
		y = float( self.widget['isocY'].text() )
		z = float( self.widget['isocZ'].text() )
		# Emit signal with all three coordinates.
		logging.debug('Emitting updateIsocenter signal.')
		self.isocenterChanged.emit(x,y,z)

class QHUSpinBox(QtWidgets.QSpinBox):
	'''CT HU windowing spinbox'''
	def __init__(self):
		super().__init__()
		self.setRange(-1000,5000)
		self.setSingleStep(100)
		self.setValue(-1000)

class QXraySpinBox(QtWidgets.QSpinBox):
	'''Xray windowing spin box'''
	def __init__(self):
		super().__init__()
		self.setRange(0,65535)
		self.setSingleStep(5000)
		self.setValue(0)

class QHLine(QtWidgets.QFrame):
	'''Horizontal line.'''
	def __init__(self):
		super().__init__()
		self.setFrameShape(QtWidgets.QFrame.QHLine)
		self.setFrameShadow(QtWidgets.QFrame.Sunken)