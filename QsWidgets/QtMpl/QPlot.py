import matplotlib as mpl
mpl.use('Qt5Agg')
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5 import QtGui, QtCore, QtWidgets
from synctools.imageGuidance import optimiseFiducials
from functools import partial
import logging

# For PyInstaller:
import sys, os
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the pyInstaller bootloader extends the sys module by a flag frozen=True and sets the app path into variable _MEIPASS'.
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))
resourceFilepath = application_path+'/resources/'

__all__ = ['QPlot','QHistogramWindow','QEditableIsocenter']

class QPlot(QtCore.QObject):
	'''
	Documentation for now:
	- imageLoad(filename, pixelsize, oreitnation, imagenumber(/2), fileformat): Load image into canvas.
	- imageUpdate(newdata): Send new data to canvas.
	- markerUpdate(): Called from eventFilter (cid: callbackID), appends new markers?
	- markerReset(markerspecifier): Resets the markers (either one or all).
	- eventFilter(event): Based on the event identifier we can tell it to do something.
	'''

	newIsocenter = QtCore.pyqtSignal(float,float)

	def __init__(self,tableModel):
		super().__init__()
		self.image = None
		self.plotDimensions = None
		self.pointsX = []
		self.pointsY = []
		self.i = 0
		self.markersMaximum = 0
		self.markersList = []
		self.markersListOptimised = []
		self.markerModel = tableModel
		self._radiographMode = 'sum'
		self._R = np.identity(3)
		# Axis takes on values {1: first axis, 2: second axis, 0: null axis}.
		self.axis = [1,2,0]
		self.mask = None
		self.overlay = {}
		self.machineIsocenter = [0,0]
		self.patientIsocenter = [0,0]
		self.ctd = None

		self.fig = plt.figure()
		self.fig.patch.set_facecolor('#000000')
		self.ax = self.fig.add_axes([0,0,1,1])
		self.ax.set_facecolor('#000000')
		self.ax.title.set_color('#FFFFFF')
		self.ax.xaxis.label.set_color('#FFFFFF')
		self.ax.yaxis.label.set_color('#FFFFFF')
		self.ax.xaxis.set_label_coords(0.5,0.12)
		self.ax.yaxis.set_label_coords(0.12,0.5)
		self.ax.xaxis.label.set_size(20)
		self.ax.yaxis.label.set_size(20)
		# self.ax.yaxis.label.set_rotation(90)
		self.ax.spines['left'].set_visible(False)
		self.ax.spines['top'].set_visible(False)
		self.ax.spines['right'].set_visible(False)
		self.ax.spines['bottom'].set_visible(False)
		self.ax.tick_params('both',which='both',length=7,width=1,pad=-30,direction='in',colors='#FFFFFF')

		# Create a canvas widget for Qt to use.
		self.canvas = FigureCanvas(self.fig)
		# self.canvas.setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
		# self.canvas.setCursor(QtCore.Qt.CrossCursor)
		# cursor = mpl.widgets.Cursor(self.ax, useblit=True, color='red', linewidth=2)
		# Refresh the canvas.
		self.canvas.draw()

		self.canvas._pickerActive = False

	def updatePatientIsocenter(self,_x,_y):
		# toggleOverlay
		self.patientIsocenter = [_x,_y]
		if 'patIso' in self.overlay:
			self.toggleOverlay(2,False) 
			self.toggleOverlay(2,True)
		if 'beamArea' in self.overlay:
			self.toggleOverlay(3,False) 
			self.toggleOverlay(3,True)

	def loadCoordinate(self,name,vector):
		# Pull in DICOM information in XYZ mm and turn it into the current view of the dataset.
		self.coordinate[name] = self._R@np.transpose(np.array(vector))

	def imageLoad(self,array,extent=np.array([-1,1,-1,1])):
		# Clear the canvas and start again:
		self.ax.cla()

		# Always make it float32. Always assume it is a flat 2D array.
		self.data = np.array(array,dtype=np.float32)
		self.extent = extent
		
		self.image = self.ax.imshow(self.data, cmap='bone', extent=self.extent)
		self.ax.set_xlim(extent[0:2])
		self.ax.set_ylim(extent[2:4])
		self.ax.set_aspect("equal", "datalim")
		self.canvas.draw()
		# Start Callback ID
		self.cid = self.canvas.mpl_connect('button_press_event', self.eventFilter)

	def applyWindow(self,imin,imax):
		# Set the color scale to match the window.
		try:
			self.image.set_clim(vmin=imin,vmax=imax)
			self.canvas.draw()
		except:
			pass

	def markerAdd(self,x,y):
		'''Append marker position if it is within the maximum marker limit.'''
		if self.i < self.markersMaximum:
			self.pointsX.append(x)
			self.pointsY.append(y)
			self.i += 1
			self.markerModel.addPoint(self.i,x,y)
			# Plot marker list.
			scatter = self.ax.scatter(x,y,c='r',marker='+',s=50)
			text = self.ax.text(x+1,y-3,self.i,color='r')
			self.markersList += scatter,text
			# Refresh views.
			self.canvas.draw()

	def markerUpdate(self,item):
		'''Redraw all the markers to their updated positions.'''
		# Item = qabstractitemmodel item linking to the marker to be changed.
		if self.markerModel._locked:
			pass
		else:
			for key in self.markerModel.items:
				for value in self.markerModel.items[key]:
					if value == item:
						index1 = self.markerModel.indexFromItem(self.markerModel.items[key][0])
						index2 = self.markerModel.indexFromItem(self.markerModel.items[key][1])
						x = self.markerModel.data(index1)
						y = self.markerModel.data(index2)
						# key is row which x,y is stored.
						scatter = self.ax.scatter(x,y,c='r',marker='+',s=50)
						text = self.ax.text(x+1,y-3,key+1,color='r')
						# Remove old plots.
						self.markersList[key*2].remove()
						self.markersList[key*2+1].remove()
						# Remove from list.
						self.markersList.remove(self.markersList[key*2])
						self.markersList.remove(self.markersList[key*2])
						# Insert new.
						self.markersList[key*2:key*2] = scatter,text
						self.canvas.draw()
						# Update pointsXY lists.
						self.pointsX[key] = x
						self.pointsY[key] = y

	def removeMarker(self,marker=-1):
		'''Clear the specified marker. Else clear all markers.'''
		# Remove all markers: 
		if marker == -1:
			self.i = 0
			self.pointsX = []
			self.pointsY = []
			if len(self.markersList) > 0:
				for index in range(len(self.markersList)):
					self.markersList[index].remove()
			self.markersList = []
			# Reset table values.
			self.markerModel.clearMarkers(self.markersMaximum)
			# Set to -2 to remove optimised markers as well.
			marker = -2

		elif marker == -2:
			# Remove optimised markers, if any.
			self.pointsXoptimised = []
			self.pointsYoptimised = []
			if len(self.markersListOptimised) > 0:
				for i in range(len(self.markersListOptimised)):
					self.markersListOptimised[-1].remove()
					del(self.markersListOptimised[-1])

		else: return

		self.canvas.draw()

	def markerOptimise(self,fiducialSize,threshold):
		'''Optimise markers that are selected in plot.'''
		# Remove any existing markers.
		self.removeMarker(marker=-2)

		# Call syncMRT optimise points module. Send points,data,dims,markersize.
		pointsIn = np.column_stack((self.pointsX,self.pointsY))
		extent = self.image.get_extent()
		# points = optimiseFiducials(pointsIn,self.data,extent,fiducialSize,threshold)
		points = optimiseFiducials(pointsIn,np.array(self.data),extent,fiducialSize,threshold)
		self.pointsXoptimised = points[:,0]
		self.pointsYoptimised = points[:,1]

		# Re-plot with optimised points over the top (in blue).
		self.markersListOptimised = []
		for i in range(len(self.pointsXoptimised)):
			x = self.pointsXoptimised[i]
			y = self.pointsYoptimised[i]
			# Plot marker list.
			scatter = self.ax.scatter(x,y,c='b',marker='+',s=50)
			text = self.ax.text(x+1,y-3,i+1,color='b')
			self.markersListOptimised += scatter,text

		self.canvas.draw()

	def markers(self):
		# Return the points in this plot.
		return zip(self.pointsX,self.pointsY)

	def toggleOverlay(self,overlayType,state=False):
		'''
		Single overlay function with various types.
			- 0: Centroid overaly
			- 1: Machine Isocenter overlay
			- 2: Patient Isocenter overlay
		'''
		if overlayType == 0:
			# Centroid overlay.
			if self.ctd is not None:
				# Remove overlay lines if they exist.
				if 'ctd' in self.overlay:
					for obj in self.overlay['ctd']:
						obj.remove()
					del(self.overlay['ctd'])
				if state is True:
					# Plot overlay scatter points.
					x,y = [self.ctd[a],self.ctd[b]]
					self.overlay['ctd'] = [
							self.ax.scatter(self.ctd[0],self.ctd[1],c='b',marker='+',s=50),
							self.ax.text(self.ctd[0]+1,self.ctd[1]-3,'ctd',color='b')
						]
				else:
					pass
		elif overlayType == 1:
			# Machine isocenter overlay.
			# Remove overlay lines.
			if 'machIsoH' in self.overlay:
				self.overlay['machIsoH'].remove()
				del(self.overlay['machIsoH'])
			if 'machIsoV' in self.overlay:
				self.overlay['machIsoV'].remove()
				del(self.overlay['machIsoV'])
			if state is True:
				# Plot overlay lines.
				self.overlay['machIsoV'] = self.ax.axvline(self.machineIsocenter[0],c='r',alpha=0.5)
				self.overlay['machIsoH'] = self.ax.axhline(self.machineIsocenter[1],c='r',alpha=0.5)
			else:
				pass
		elif overlayType == 2:
			# Overlay of the patient iso.
			# Remove the overlay lines.
			if 'patIso' in self.overlay:
				for obj in reversed(self.overlay['patIso']):
					obj.remove()
				del(self.overlay['patIso'])
			if state is True:
				# Create new patches.
				self.overlay['patIso'] = [
						self.ax.scatter(self.patientIsocenter[0],self.patientIsocenter[1],marker='+',color='y',s=50),
						self.ax.text(self.patientIsocenter[0]+1,self.patientIsocenter[1]-3,'ptv',color='y')
					]
			else:
				pass
		elif overlayType == 3:
			# Remove it first if it already exists.
			if 'beamArea' in self.overlay:
				self.overlay['beamArea'].remove()
				del(self.overlay['beamArea'])
			# Beam area overlay.
			if state is True:
				# Create new patches.
				_maskSize = 5
				_beam = Rectangle((-_maskSize/2,-_maskSize/2), _maskSize, _maskSize,fc='r',ec='none')
				_ptv = Rectangle((self.patientIsocenter[0]-_maskSize/2,self.patientIsocenter[1]-_maskSize/2), _maskSize, _maskSize,fc='y',ec='none')
				pc = PatchCollection([_beam,_ptv],alpha=0.2,match_original=True)
				self.overlay['beamArea'] = self.ax.add_collection(pc)
			else:
				pass
		# Update the canvas.
		self.canvas.draw()

	def setExtent(self,newExtent):
		# Change extent and markers.
		change = newExtent-self.extent

		''' Update markers '''
		# Get values and add changes.
		for i in range(len(self.pointsX)):
			self.pointsX[i] -= change[0]
			self.pointsY[i] -= change[2]

		x,y = self.pointsX,self.pointsY
		
		# Remove markers
		self.removeMarker()
		# Add new points
		for i in range(len(x)):
			self.markerAdd(x[i],y[i])

		# Update extent
		self.extent = newExtent
		self.image.set_extent(self.extent)

		# Refresh
		self.canvas.draw()

	def eventFilter(self,event):
		# If mouse button 1 is clicked (left click).
		if (event.button == 1) & (self.canvas._pickerActive):
			self.markerAdd(event.xdata,event.ydata)
		elif (event.button == 1) & (self.canvas._isocenterPickerActive):
			self.newIsocenter.emit(event.xdata,event.ydata)
			self.canvas._isocenterPickerActive = False


CSS_CENTER_HEADING = """
QGroupBox::title {
	subcontrol-origin: margin;
	subcontrol-position: top;
}
"""

class QHistogramWindow(QtWidgets.QGroupBox):
	windowUpdated = QtCore.pyqtSignal(int,int)

	def __init__(self):
		super().__init__()
		# Create histogram plot.
		self.histogram = Histogram()
		# Sliders.
		self.range = []
		self.range.append(QtWidgets.QSlider(QtCore.Qt.Horizontal))
		self.range.append(QtWidgets.QSlider(QtCore.Qt.Horizontal))
		# Flattening method buttons.
		self.button = []
		self.button.append(QtWidgets.QRadioButton('Sum'))
		self.button.append(QtWidgets.QRadioButton('Max'))
		# Layout.
		layout = QtWidgets.QVBoxLayout()
		layout.setContentsMargins(0,0,0,0)
		layout.setSpacing(0)
		layout.addWidget(self.histogram.canvas)
		layout.addWidget(self.range[0])
		layout.addWidget(self.range[1])
		# layout.addWidget(options)
		# Set layout.
		self.setLayout(layout)
		self.setStyleSheet(CSS_CENTER_HEADING)

		# When sliders change update histogram.
		for i in range(len(self.range)):
			self.range[i].valueChanged.connect(self.updateHistogram)
			self.range[i].sliderReleased.connect(self.updatePlot)

	def updateHistogram(self):
		self.histogram.update(self.range[0].value(), self.range[1].value())

	def updatePlot(self):
		self.windowUpdated.emit(self.range[0].value(), self.range[1].value())

	def setData(self,data):
		# Give histogram the data to work with.
		self.histogram.loadImage(data)
		# Give the slider widgets a max and min value to work with.
		vmin = np.min(data)
		vmax = np.max(data)
		for i in range(len(self.range)):
			self.range[i].setMinimum(vmin)
			self.range[i].setMaximum(vmax)
		self.range[0].setValue(vmin)
		self.range[1].setValue(vmax)

	def setEnabled(self,state):
		for i in range(len(self.range)):
			self.range[i].setEnabled(state)
		for i in range(len(self.button)):
			self.button[i].setEnabled(state)

class Histogram:
	def __init__(self):
		# super().__init__()
		# A figure instance to plot on.
		self.figure = plt.figure()
		# This is the Canvas Widget that displays the `figure`.
		self.canvas = FigureCanvas(self.figure)
		# Add axes for plotting on.
		self.ax = self.figure.add_axes([0,0,1,1])
		# Draw the canvas.
		self.canvas.draw()

	def loadImage(self,data,**kwargs):
		# Data min and max.
		dmin = np.min(data)
		dmax = np.max(data)
		# Take the data and make a histogram.
		nbins = kwargs.get('nbins',64)
		histogramValues,_,_ = self.ax.hist(data.ravel(),facecolor='k',alpha=0.5,bins=nbins)
		self.hmax = np.max(histogramValues)
		# Draw lines over the plot.
		self.ax.plot([dmin,dmax],[0,self.hmax],'k-',lw=1)
		self.ax.plot([dmax,dmax],[0,self.hmax],'k--',lw=1)

	def update(self,rmin,rmax):
		'''Update the histogram scale line to match the sliders.'''
		# Remove old lines.
		for i in range(len(self.ax.lines)):
			# This will recursively remove the first line until there are no lines left.
			self.ax.lines[0].remove()
		# Add new lines.
		self.ax.plot([rmin,rmax],[0,self.hmax],'k-', lw=1)
		self.ax.plot([rmax,rmax],[0,self.hmax],'k--', lw=1)
		# Redraw.
		self.canvas.draw()


class QEditableIsocenter(QtWidgets.QGroupBox):
	isocenterUpdated = QtCore.pyqtSignal(float,float)
	selectIsocenter = QtCore.pyqtSignal()

	def __init__(self,_x,_y):
		super().__init__()
		# Stylesheet.
		# _css = open(resourceFilepath+'QPlot.css')
		# self.setStyleSheet(_css.read())
		# Header widget.
		_header = QtWidgets.QWidget()
		self.select = QtWidgets.QPushButton()
		self.select.setIcon(QtGui.QIcon(resourceFilepath+'pick.png'))
		self.select.setCheckable(True)
		self.select.setChecked(False)
		self.select.setMaximumWidth(38)
		# self.select.setObjectName('isocenterPicker')
		self.select.setToolTip("Select treatment isocentre with a mouse click.")
		_layout = QtWidgets.QHBoxLayout()
		_layout.setContentsMargins(0,0,0,0)
		_layout.addWidget(QtWidgets.QLabel("Treatment Isocenter"),QtCore.Qt.AlignLeft)
		_layout.addWidget(self.select,QtCore.Qt.AlignRight)
		_header.setLayout(_layout)
		# Labels.
		_xlbl = QtWidgets.QLabel('x (mm): ')
		_ylbl = QtWidgets.QLabel('y (mm): ')
		# Create line edits.
		self.x = QtWidgets.QLineEdit(str(_x))
		self.y = QtWidgets.QLineEdit(str(_y))
		# Flattening method buttons.
		validator = QtGui.QDoubleValidator()
		validator.setBottom(-150)
		validator.setTop(150)
		validator.setDecimals(2)
		# Set validators.
		self.x.setValidator(validator)
		self.y.setValidator(validator)
		# Layout.
		layout = QtWidgets.QFormLayout()
		layout.setContentsMargins(5,0,0,0)
		layout.addRow(_header)
		layout.addRow(_xlbl,self.x)
		layout.addRow(_ylbl,self.y)
		# Set layout.
		self.setLayout(layout)
		# Signals and slots.
		self.select.clicked.connect(self._selectIsocenter)
		self.x.editingFinished.connect(self.updateIsocenter)
		self.y.editingFinished.connect(self.updateIsocenter)

	def updateIsocenter(self):
		""" Send a signal with updated x,y coordinates. """
		_x = float(self.x.text())
		_y = float(self.y.text())
		self.isocenterUpdated.emit(_x,_y)

	def _selectIsocenter(self):
		"""
		Other way of setting color:
		palette = self.select.palette()
		palette.setColor(QtGui.QPalette.Button,QtGui.QColor('#82FF70'))
		self.select.setPalette(palette)
		"""
		if self.select.isChecked():
			self.select.setDown(True)
		else:
			self.select.setDown(False)
		# self.select.setDown(True)
		self.selectIsocenter.emit()

	def setIsocenter(self,x,y):
		""" Set the isocenter based off x and y coordinates. """
		self.select.setDown(False)
		self.select.setChecked(False)
		self.x.setText("{:.2f}".format(x))
		self.y.setText("{:.2f}".format(y))
		self.x.editingFinished.emit()
		self.y.editingFinished.emit()
