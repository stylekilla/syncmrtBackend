# Qt widgets.
from PyQt5 import QtWidgets, QtGui, QtCore
# Matplotlib widgets.
import matplotlib as mpl
mpl.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT

resourceFilepath = "resources/"

class QsPlotEnvironment(QtWidgets.QWidget):
	'''
	An advanced QWidget specifically designed for plotting with MatPlotLib.
	It has a navbar, plot and table.
	'''
	def __init__(self,**kwargs):
		super().__init__()
		labels = {
			'xLabel':kwargs.get('xLabel','X'),
			'yLabel':kwargs.get('yLabel','Y')
		}
		# A table model is required for the table view.
		self.tableModel = iQPlotTableModel(labels)
		self.tableView = QtWidgets.QTableView()
		# The plot needs the table model for data.
		self.plot = widgets.mpl.plot(self.tableModel)
		# The navbar needs the plot widget and the parent widget.
		self.navbar = iQNavigationBar(self.plot.canvas)

		# Configure table view.
		self.tableView.setAlternatingRowColors(True)
		self.tableView.setModel(self.tableModel)
		self.tableView.setColumnWidth(0,200)
		self.tableView.verticalHeader().setDefaultSectionSize(20)
		self.tableView.verticalHeader().hide()
		self.tableView.horizontalHeader().setStretchLastSection(True)
		
		# Add layout to parent.
		layout = QtWidgets.QVBoxLayout()
		# Add widgets to layout.
		layout.addWidget(self.navbar)
		# QSplitter for resizing between plot and table.
		splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
		splitter.addWidget(self.plot.canvas)
		splitter.addWidget(self.tableView)
		# Set stretch factors.
		splitter.setSizes([200,100])
		# splitter.setStretchFactor(0,0.5)
		# splitter.setStretchFactor(1,0.5)
		# Add splitter to layout.
		layout.addWidget(splitter)
		# Add layout to widget.
		self.setLayout(layout)

	def setRadiographMode(self,mode):
		'''Set radiograph mode to 'sum' or 'max.''' 
		self.plot._radiographMode = mode

	def settings(self,setting,value):
		if setting == 'maxMarkers':
			self.plot.markerModel.setMarkerRows(value)
			self.plot.markersMaximum = value
		else:
			pass

	def updatePatientIsocenter(self,newIsoc):
		# Update value in plot.
		self.plot.patientIsocenter = newIsoc
		# Refresh plot by toggling overlay off/on.
		self.plot.toggleOverlay(2,False)
		self.plot.toggleOverlay(2,True)

class QsPlotTableModel(QtGui.QStandardItemModel):
	'''
	Table model for plot points inside the MPL canvas. This is designed to dynamically add and remove data points as they 
	are selected or removed.
	Markers are stored in dict with x,y vals.
	The model will always have a limit of rows set by the maximum marker condition/setting.
	'''
	def __init__(self,labels):
		# Initialise the standard item model first.
		super().__init__()
		# Set column and row count.
		self.setColumnCount(3)
		self.setMarkerRows(0)
		self.items = {}
		self._locked = False

		self.setHorizontalHeaderLabels([
			'#',
			labels.get('xLabel','x'),
			labels.get('yLabel','y')
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

	def clearMarkers(self,newRows):
		'''Clear the model of all it's rows and re-add empty rows in their place.'''
		currentRows = self.rowCount()
		self.removeRows(0,currentRows)
		self.setMarkerRows(newRows)

class QsNavigationBar(NavigationToolbar2QT):
	def __init__(self,canvas):
		NavigationToolbar2QT.__init__(self,canvas,parent=None)
		self.canvas = canvas

		actions = self.findChildren(QtWidgets.QAction)
		toolsBlacklist = ['Customize','Forward','Back','Subplots','Save']
		for a in actions:
			if a.text() in toolsBlacklist:
				self.removeAction(a)

		# Remove the labels (x,y,val).
		self.locLabel.deleteLater()

		self.actionPickMarkers = self.addAction('Pick')
		self.actionClearMarkers = self.addAction('Clear')
		self.actionImageSettings = self.addAction('Image Settings')
		self.insertSeparator(self.actionImageSettings)
		self.actionPickMarkers.setCheckable(True)

		# Pick should disable when ZOOM or PAN is enabled.

	def set_message(self, s):
		# Set empty message method to stop it from trying to use self.locLabel
		pass 

	def pick(self):
		if self._active == 'PICK':
			self._active = None
		else:
			self._active = 'PICK'

		if self._idPress is not None:
			self._idPress = self.canvas.mpl_disconnect(self._idPress)
			self.mode = ''

		if self._active:
			self.canvas._pickerActive = True
			self._idPress = self.canvas.mpl_connect(
				'button_press_event', self.press_pick)
			self.canvas.widgetlock(self)
		else:
			self.canvas.widgetlock.release(self)
			self.canvas._pickerActive = False

	def press_pick(self, event):
		"""the press mouse button in pick mode callback"""

		if event.button == 1:
			self._button_pressed = 1
		else:
			self._button_pressed = None
			return

		self.press(event)
		self.release(event)


class QsStacedkWidget(QtWidgets.QStackedWidget):
	def __init__(self,parent):
		super().__init__()
		self.parent = parent
		self.setMinimumHeight(500)
		self.setFixedWidth(225)
		sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.MinimumExpanding)
		self.setSizePolicy(sizePolicy)
		self.parent.setVisible(False)
		self.stackDict = {}

		layout = QtWidgets.QGridLayout()
		layout.addWidget(self)
		layout.setContentsMargins(0,0,0,0)
		parent.setLayout(layout)

	def addPage(self,pageName,before=None,after=None):
		'''Before and after must be names of other pages.'''
		self.stackDict[pageName] = QtWidgets.QWidget()

		if before is not None:
			if before == 'all':
				index = 0
			else:
				index = self.indexOf(self.stackDict[before])

		elif after is not None:
			if after == 'all':
				index = self.count()
			else:
				index = self.indexOf(self.stackDict[after]) + 1
		else:
			index = self.count()

		self.insertWidget(index,self.stackDict[pageName])

	def removePage(self,pageName,delete=False):
		'''Remove page from stack, delete from memory if required.'''
		self.removeWidget(self.stackDict[pageName])
		if delete: del self.stackDict[pageName]

class QsListWidget(QtWidgets.QListWidget):
	def __init__(self,parent):
		# List initialisation.
		super().__init__()
		self.setMinimumHeight(500)
		self.setFixedWidth(60)
		sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.MinimumExpanding)
		self.setSizePolicy(sizePolicy)
		self.setIconSize(QtCore.QSize(50,50))
		# A list of pageNames in the stacked widget (of pages to show and hide).
		self.listDict = {}

		# Add self to parent layout.
		layout = QtWidgets.QGridLayout()
		layout.addWidget(self)
		layout.setContentsMargins(0,0,0,0)
		parent.setLayout(layout)

	def addPage(self,pageName,before=None,after=None):
		'''Before and after must be names of other pages.'''
		self.listDict[pageName] = QtWidgets.QListWidgetItem()
		self.listDict[pageName].setText(pageName)
		# Add Icon.
		icon = QtGui.QIcon(resourceFilepath+pageName+'.png')
		icon.pixmap(50,50)
		self.listDict[pageName].setIcon(icon)
		self.listDict[pageName].setSizeHint(QtCore.QSize(60,60))

		if before is not None:
			if before == 'all':
				index = 0
			else:
				index = self.row(self.listDict[before]) - 1
		elif after is not None:
			if after == 'all':
				index = self.count()
			else:
				index = self.row(self.listDict[after]) + 1
		else:
			index = self.count()

		self.insertItem(index,self.listDict[pageName])

	def removePage(self,pageName,delete=False):
		'''Remove page from list, delete from memory if required.'''
		self.removeItemWidget(self.listDict[pageName])

		if delete:
			del self.listDict[pageName]