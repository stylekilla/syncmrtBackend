# Qt widgets.
from PyQt5 import QtWidgets, QtGui, QtCore
from synctools.QsWidgets import QtMpl
# Matplotlib widgets.
import matplotlib as mpl
mpl.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT

import logging
from functools import partial

# For PyInstaller:
import sys, os
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the pyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app 
    # path into variable _MEIPASS'.
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))
image_path = application_path+'synctools/QsWidgets/QtMpl/images/'

class QPlotEnvironment(QtWidgets.QWidget):
	'''
	An advanced widget specifically designed for plotting with MatPlotLib in Qt5.
	It has a navbar, plot and table.
	'''
	toggleSettings = QtCore.pyqtSignal()

	def __init__(self):
		# Start as a blank layout.
		super().__init__()
		self.layout = QtWidgets.QHBoxLayout()
		self.layout.setContentsMargins(0,0,0,0)
		self.setLayout(self.layout)
		# Empty lists.
		self.navbar = []
		self.plot = []
		self.tableModel = []
		self.tableView = []
		self.histogram = []

	def loadImage(self,image):
		'''Load up to 2 images and send to plot.'''
		amount = len(image)
		if amount not in {1,2}:
			# Throw error.
			logging.critical('synctools.QsWidgets.QPlotEnvironment: Can only create a maximum of 2 subplots, attempted to create ',len(image))
			return

		# First create the blank subplots.
		self.addSubplot(amount)
		# Now load the images into the subplots.
		for i in range(amount):
			self.plot[i].imageLoad(image[i].pixelArray,image[i].extent)
			self.tableModel[i].setLabels(image[i].view)
			self.histogram[i].setTitle('View: '+image[i].view['title'])
			self.histogram[i].setData(image[i].pixelArray)

	def addSubplot(self,amount):
		# Can only have a maximum of 2 subplots as per loadImage().
		for i in range(amount):
			subplotWidget = QtWidgets.QWidget()
			# A table model is required for the table view.
			self.tableModel.append(QPlotTableModel())
			self.tableView.append(QtWidgets.QTableView())
			# The plot needs the table model for data.
			self.plot.append(QtMpl.QPlot(self.tableModel[i]))
			# The navbar needs the plot widget and the parent widget.
			self.navbar.append(QNavigationBar(self.plot[i].canvas))
			self.navbar[i].toggleImageSettings.connect(self.toggleImageSettings)
			self.navbar[i].clearAll.connect(self.plot[i].removeMarker)
			# Configure table view.
			self.tableView[i].setAlternatingRowColors(True)
			self.tableView[i].setModel(self.tableModel[i])
			self.tableView[i].setColumnWidth(0,200)
			self.tableView[i].verticalHeader().setDefaultSectionSize(20)
			self.tableView[i].verticalHeader().hide()
			self.tableView[i].horizontalHeader().setStretchLastSection(True)
			# Create layout for subplot widget.
			subplotLayout = QtWidgets.QVBoxLayout()
			subplotLayout.setContentsMargins(0,0,0,0)
			# Add widgets to layout.
			subplotLayout.addWidget(self.navbar[i])
			# QSplitter for resizing between plot and table.
			splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
			splitter.addWidget(self.plot[i].canvas)
			splitter.addWidget(self.tableView[i])
			# Set stretch factors.
			splitter.setSizes([200,100])
			# Add splitter to layout.
			subplotLayout.addWidget(splitter)
			# Add layout to widget.
			subplotWidget.setLayout(subplotLayout)
			# Add widget to plotenvironment.
			self.layout.addWidget(subplotWidget)
			# Create a histogram widget for the plot.
			self.histogram.append(QtMpl.QHistogramWindow())
			# When histogram changed then update plot.
			self.histogram[i].windowUpdated.connect(partial(self.plot[i].applyWindow))

	def getPlotHistogram(self):
		return self.histogram

	def setRadiographMode(self,mode):
		'''Set radiograph mode to 'sum' or 'max.''' 
		self.plot[i]._radiographMode = mode

	def settings(self,setting,value):
		if setting == 'maxMarkers':
			for i in range(len(self.plot)):
				self.plot[i].markerModel.setMarkerRows(value)
				self.plot[i].markersMaximum = value
		else:
			pass

	def updatePatientIsocenter(self,newIsoc):
		for i in range(len(self.plot)):
			# Update value in plot.
			self.plot[i].patientIsocenter = newIsoc
			# Refresh plot by toggling overlay off/on.
			self.plot[i].toggleOverlay(2,False)
			self.plot[i].toggleOverlay(2,True)

	def toggleOverlay(self,overlay,state):
		for i in range(len(self.plot)):
			# Overlay = 0 (ctd), 1 (mach iso), 2 (pat iso)
			self.plot[i].toggleOverlay(overlay,state)

	def toggleImageSettings(self):
		self.toggleSettings.emit()

	def resetWidget(self):
		# Removes all widgets and items associated with the layout. Essentially creates a new one.
		self.__init__()

class QPlotTableModel(QtGui.QStandardItemModel):
	'''
	Table model for plot points inside the MPL canvas. This is designed to dynamically add and remove data points as they 
	are selected or removed.
	Markers are stored in dict with x,y vals.
	The model will always have a limit of rows set by the maximum marker condition/setting.
	'''
	def __init__(self,labels={}):
		# Initialise the standard item model first.
		super().__init__()
		# Set column and row count.
		self.setColumnCount(3)
		self.setMarkerRows(0)
		self.items = {}
		self._locked = False
		self.setHorizontalHeaderLabels([
			labels.get('title','-'),
			labels.get('xLabel','-'),
			labels.get('yLabel','-')
		])

	def addPoint(self,row,x,y):
		'''Write a point to the model. This is specified by the point number (identifier), and it's x and y coord.'''
		self._locked = True
		column0 = QtGui.QStandardItem()
		column0.setData('Marker '+str(row),QtCore.Qt.DisplayRole)
		column0.setEditable(False)

		column1 = QtGui.QStandardItem()
		column1.setData(float(x),QtCore.Qt.DisplayRole)

		column2 = QtGui.QStandardItem()
		column2.setData(float(y),QtCore.Qt.DisplayRole)

		self.items[row-1] = [column1, column2]
		# self.markers[row-1] = [x,y]

		data = [column0, column1, column2]

		for index, element in enumerate(data):
			self.setItem(row-1,index,element)

		self.layoutChanged.emit()
		self._locked = False

	def removePoint(self,index):
		'''Remove a specific point in the list.'''
		pass

	def setMarkerRows(self,rows):
		'''Defines the maximum number of rows according to the maximum number of markers.'''
		current = self.rowCount()
		difference = abs(current-rows)

		if rows < current:
			self.removeRows(current-1-difference, difference)
		elif rows > current:
			self.insertRows(current,difference)
		else:
			pass
		self.layoutChanged.emit()

	def setLabels(self,labels):
		# Set the column header labels.
		self.setHorizontalHeaderLabels([
			'View: '+labels.get('title','Unknown?'),
			labels.get('xLabel','X?'),
			labels.get('yLabel','Y?')
		])

	def clearMarkers(self,newRows):
		'''Clear the model of all it's rows and re-add empty rows in their place.'''
		currentRows = self.rowCount()
		self.removeRows(0,currentRows)
		self.setMarkerRows(newRows)

class QNavigationBar(NavigationToolbar2QT):
	clearAll = QtCore.pyqtSignal()
	toggleImageSettings = QtCore.pyqtSignal()

	def __init__(self,canvas):
		self.toolitems = (
				('Home', 'Reset original view', 'home', 'home'),
				('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
				('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
				('Pick', 'Click to select marker', 'help', 'pick'),
				('Clear', 'Clear all the markers', 'help', 'clear'),
				# ('Settings', 'Show the image settings', 'help', 'settings'),
				(None, None, None, None),
				('Save', 'Save the figure', 'filesave', 'save_figure'),
			)
		self.basedir = image_path
		NavigationToolbar2QT.__init__(self,canvas,parent=None)
		self.canvas = canvas

		# actions = self.findChildren(QtWidgets.QAction)
		# toolsBlacklist = ['Customize','Forward','Back','Subplots','Save']
		# toolsBlacklist = ['Customize','Forward','Back','Subplots']
		# for a in actions:
			# if a.text() in toolsBlacklist:
				# self.removeAction(a)

		# Remove the labels (x,y,val).
		self.locLabel.deleteLater()
		# Add my own actions to the toolbar.
		# self._actions['pick'] = self.addAction('pick')
		# self._actions['pick'].setCheckable(True)
		# self._actions['clear'] = self.addAction('clear')
		# self._actions['settings'] = self.addAction('settings')
		# self.insertSeparator(self._actions['settings'])

		# Pick should disable when ZOOM or PAN is enabled.

	def _update_buttons_checked(self):
		# sync button checkstates to match active mode
		self._actions['pan'].setChecked(self._active == 'PAN')
		self._actions['zoom'].setChecked(self._active == 'ZOOM')
		self._actions['pick'].setChecked(self._active == 'PICK')
		if self._active == 'PICK':
			self.canvas._pickerActive = True
		else:
			self.canvas._pickerActive = False

	def set_message(self, s):
		# Set empty message method to stop it from trying to use self.locLabel
		pass 

	def pick(self,*args):
		if self._active == 'PICK':
			self._active = None
		else:
			self._active = 'PICK'
		if self._idPress is not None:
			self._idPress = self.canvas.mpl_disconnect(self._idPress)
			self.mode = ''
		if self._active:
			# Set the cursor.
			self.canvas._pickerActive = True
			self._idPress = self.canvas.mpl_connect(
				'button_press_event', self.press_pick)
			self.canvas.widgetlock(self)
		else:
			self.canvas.widgetlock.release(self)
		self._update_buttons_checked()

	def press_pick(self, event):
		"""the press mouse button in pick mode callback"""
		if event.button == 1:
			self._button_pressed = 1
		else:
			self._button_pressed = None
			return
		# Press and then release the button.
		self.press(event)
		self.release(event)

	def clear(self):
		self.clearAll.emit()
	
	def settings(self):
		self.toggleImageSettings.emit()