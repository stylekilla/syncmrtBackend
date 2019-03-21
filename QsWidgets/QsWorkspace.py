# Qt widgets.
from PyQt5 import QtWidgets, QtGui, QtCore
from synctools.QsWidgets import QtMpl
# Matplotlib widgets.
import matplotlib as mpl
mpl.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT

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
		self.tableModel = QPlotTableModel(labels)
		self.tableView = QtWidgets.QTableView()
		# The plot needs the table model for data.
		self.plot = QtMpl.QPlot(self.tableModel)
		# The navbar needs the plot widget and the parent widget.
		self.navbar = QNavigationBar(self.plot.canvas)

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

class QPlotTableModel(QtGui.QStandardItemModel):
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

class QNavigationBar(NavigationToolbar2QT):
	def __init__(self,canvas):
		self.toolitems = (
				('Home', 'Reset original view', 'home', 'home'),
				('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
				('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
				('Pick', 'Click to select marker', 'help', 'pick'),
				('Clear', 'Clear all the markers', 'help', 'clear'),
				('Settings', 'Show the image settings', 'help', 'settings'),
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
		pass
	
	def settings(self):
		pass

# toolitems = (
#     ('Home', 'Reset original view', 'home', 'home'),
#     ('Back', 'Back to previous view', 'back', 'back'),
#     ('Forward', 'Forward to next view', 'forward', 'forward'),
#     (None, None, None, None),
#     ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
#     ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
#     ('Subplots', 'Configure subplots', 'subplots', 'configure_subplots'),
#     (None, None, None, None),
#     ('Save', 'Save the figure', 'filesave', 'save_figure'),
#   )
# def pan(self, *args):
#     """Activate the pan/zoom tool. pan with left button, zoom with right"""
#     # set the pointer icon and button press funcs to the
#     # appropriate callbacks

#     if self._active == 'PAN':
#         self._active = None
#     else:
#         self._active = 'PAN'
#     if self._idPress is not None:
#         self._idPress = self.canvas.mpl_disconnect(self._idPress)
#         self.mode = ''

#     if self._idRelease is not None:
#         self._idRelease = self.canvas.mpl_disconnect(self._idRelease)
#         self.mode = ''

#     if self._active:
#         self._idPress = self.canvas.mpl_connect(
#             'button_press_event', self.press_pan)
#         self._idRelease = self.canvas.mpl_connect(
#             'button_release_event', self.release_pan)
#         self.mode = 'pan/zoom'
#         self.canvas.widgetlock(self)
#     else:
#         self.canvas.widgetlock.release(self)

#     for a in self.canvas.figure.get_axes():
#         a.set_navigate_mode(self._active)

#     self.set_message(self.mode)

# def press_pan(self, event):
#     """Callback for mouse button press in pan/zoom mode."""

#     if event.button == 1:
#         self._button_pressed = 1
#     elif event.button == 3:
#         self._button_pressed = 3
#     else:
#         self._button_pressed = None
#         return

#     if self._nav_stack() is None:
#         # set the home button to this view
#         self.push_current()

#     x, y = event.x, event.y
#     self._xypress = []
#     for i, a in enumerate(self.canvas.figure.get_axes()):
#         if (x is not None and y is not None and a.in_axes(event) and
#                 a.get_navigate() and a.can_pan()):
#             a.start_pan(x, y, event.button)
#             self._xypress.append((a, i))
#             self.canvas.mpl_disconnect(self._idDrag)
#             self._idDrag = self.canvas.mpl_connect('motion_notify_event',
#                                                    self.drag_pan)

#     self.press(event)
# def release_pan(self, event):
#     """Callback for mouse button release in pan/zoom mode."""

#     if self._button_pressed is None:
#         return
#     self.canvas.mpl_disconnect(self._idDrag)
#     self._idDrag = self.canvas.mpl_connect(
#         'motion_notify_event', self.mouse_move)
#     for a, ind in self._xypress:
#         a.end_pan()
#     if not self._xypress:
#         return
#     self._xypress = []
#     self._button_pressed = None
#     self.push_current()
#     self.release(event)
#     self.draw()
