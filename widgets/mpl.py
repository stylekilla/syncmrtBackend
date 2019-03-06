import matplotlib as mpl
mpl.use('Qt5Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5 import QtGui, QtCore, QtWidgets
from synctools.imageGuidance import optimiseFiducials

# from skimage import exposure
from skimage.external import tifffile as tiff

class plot:
	'''
	Documentation for now:
	- imageLoad(filename, pixelsize, oreitnation, imagenumber(/2), fileformat): Load image into canvas.
	- imageUpdate(newdata): Send new data to canvas.
	- markerUpdate(): Called from eventFilter (cid: callbackID), appends new markers?
	- markerReset(markerspecifier): Resets the markers (either one or all).
	- eventFilter(event): Based on the event identifier we can tell it to do something.
	'''

	def __init__(self,model):
		self.logMessage = ()
		self.logRank = ()
		self.image = None
		self.plotDimensions = None
		self.pointsX = []
		self.pointsY = []
		self.i = 0
		self.markersMaximum = 0
		self.markersList = []
		self.markersListOptimised = []
		self.markerModel = model
		self._radiographMode = 'sum'

		self.overlay = {}
		self.machineIsocenter = [0,0,0]
		self.patientIsocenter = [0,0,0]
		self.ctd = None

		self.fig = plt.figure()
		self.fig.patch.set_facecolor('#000000')
		self.ax = self.fig.add_axes([0,0,1,1])
		# self.ax.set_axis_bgcolor('#000000')
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
		cursor = mpl.widgets.Cursor(self.ax, useblit=True, color='red', linewidth=2)
		# Refresh the canvas.
		self.canvas.draw()

		self.canvas._pickerActive = False

	def imageLoad(self,array,extent=np.array([-1,1,-1,1]),imageOrientation='',imageIndex=0):
		# Clear the canvas and start again:
		self.ax.cla()
		# Load the image.
		self.imageIndex = imageIndex
		self.data3d = np.array(array,dtype=np.float32)

		if len(self.data3d.shape) == 3:
			# 3D Image (CT/MRI etc).
			if imageIndex == 0:
				self.data2d = np.sum(self.data3d,axis=2)
				# Extent is L,R,B,T
				self.extent = extent[:4]
			elif imageIndex == 1:
				self.data2d = np.sum(self.data3d,axis=1)
				self.extent = np.concatenate((extent[4:6],extent[2:4]))
		else:
			# 2D Image (General X-ray).
			self.data2d = np.array(self.data3d)
			self.extent = extent

		self.data = np.array(self.data2d)

		# Rescale 2d image between 0 and 65535 (16bit)
		# self.imageNormalise()
			
		# if imageOrientation == 'HFS':
		# 	if imageIndex == 0:
		# 		self.ax.set_title('HFS')
		# 	if imageIndex == 1:
		# 		self.ax.set_title('HFS1 lol?')
		# elif imageOrientation == 'FHS':
		# 	if imageIndex == 0:
		# 		self.ax.set_title('FHS')
		# 	if imageIndex == 1:
		# 		self.ax.set_title('FHS1 lol?')
		# else:
		# 	if imageIndex == 0:
		# 		self.ax.set_title('Normal')
		# 		self.ax.set_xlabel('S')
		# 		self.ax.set_ylabel('L')
		# 		self.ax.text(0.95, 0.5, 'R',transform=self.ax.transAxes,color='green', fontsize=10)
		# 	if imageIndex == 1:
		# 		self.ax.set_title('Orthogonal')
		# 		self.ax.set_xlabel('S')
		# 		self.ax.set_ylabel('A')

		self.image = self.ax.imshow(self.data, cmap='bone', extent=self.extent)
		self.ax.set_xlim(extent[0:2])
		self.ax.set_ylim(extent[2:4])
		self.ax.set_aspect("equal", "datalim")
		self.canvas.draw()
		# Start Callback ID
		self.cid = self.canvas.mpl_connect('button_press_event', self.eventFilter)

	# def imageWindow(self,windows):
	# 	'''Mask 3D array, flatten and redraw 2D array. windows as List of Lists(upper and lower limit)'''
	# 	conditions = ''
	# 	for window in windows:
	# 		conditions += '((self.data3d>'+str(window[0])+')&(self.data3d<'+str(window[1])+'))|'
	# 	conditions = conditions[:-1]
	# 	mask = eval(conditions)
	# 	self.data = self.data3d*mask

	# 	if self.imageIndex == 0:
	# 		direction = 2
	# 	elif self.imageIndex == 1:
	# 		direction = 1
			
	# 	if self._radiographMode == 'max':
	# 		self.data = np.amax(self.data,axis=direction)
	# 	elif self._radiographMode == 'sum':
	# 		self.data = np.sum(self.data,axis=direction)
	# 	else:
	# 		pass

	# 	# Rescale 2d image between 0 and 65535 (16bit)
	# 	self.imageNormalise(mask=True)
	# 	self.image.set_data(self.data)
	# 	self.image.set_clim(vmin=self.data.min())
	# 	self.image.set_clim(vmax=self.data.max())
	# 	self.canvas.draw()

	# def imageNormalise(self,lower=0,upper=65535,mask=False):
	# 	# 16-bit image: 65536 levels.
	# 	maximum = np.amax(self.data)
	# 	if mask:
	# 		# Find second smallest number (assuming smallest is now zero due to earlier masking).
	# 		try:
	# 			minimum = np.unique(self.data)[1]
	# 		except: 
	# 			minimum = np.amin(self.data)

	# 	else:
	# 		minimum = np.amin(self.data)

	# 	test = np.absolute(maximum-minimum)
	# 	if test == 0:
	# 		test = 1

	# 	scale = (upper-lower)/test

	# 	self.data = (self.data - minimum)*scale
		# self.data[self.data<0] = 0

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

	def markerRemove(self,marker=-1):
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
		self.markerRemove(marker=-2)

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
				if state is True:
					# Get image index for isoc numbers.
					if self.imageIndex == 0:
						a = 1
						b = 2
					elif self.imageIndex == 1:
						a = 0
						b = 2
					# Plot overlay scatter points.
					x,y = [self.ctd[a],self.ctd[b]]
					self.overlay['ctd'] = self.ax.scatter(x,y,c='b',marker='+',s=50)
					self.overlay['ctdLabel'] = self.ax.text(x+1,y-3,'ctd',color='b')
				else:
					# Remove overlay scatter points.
					try:
						# This prevents a crash where the centroid is calculated whilst the overlay is toggled on and then attempts to toggle off.
						self.overlay['ctd'].remove()
						self.overlay['ctdLabel'].remove()
					except:
						pass

		elif overlayType == 1:
			# Machine isocenter overlay.
			if state is True:
				# Get image index for isoc numbers.
				if self.imageIndex == 0:
					a = 1
					b = 2
				elif self.imageIndex == 1:
					a = 0
					b = 2
				# Plot overlay lines.
				self.overlay['machIsoV'] = self.ax.axvline(self.machineIsocenter[a],c='g',alpha=0.5)
				self.overlay['machIsoH'] = self.ax.axhline(self.machineIsocenter[b],c='g',alpha=0.5)
			else:
				# Remove overlay lines.
				self.overlay['machIsoH'].remove()
				self.overlay['machIsoV'].remove()

		elif overlayType == 2:
			# Machine isocenter overlay.
			if state is True:
				# Get image index for isoc numbers.
				if self.imageIndex == 0:
					a = 0
					b = 1
				elif self.imageIndex == 1:
					a = 2
					b = 1
				# Plot overlay lines.
				# Plot overlay scatter points.
				x,y = [self.patientIsocenter[a],self.patientIsocenter[b]]
				self.overlay['patIso'] = self.ax.scatter(x,y,c='g',marker='+',s=50)
				self.overlay['patIsoLabel'] = self.ax.text(x+1,y-3,'ptv',color='g')
			else:
				try:
					# Remove overlay lines.
					self.overlay['patIso'].remove()
					self.overlay['patIsoLabel'].remove()
				except:
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

		# for key,val in self.pointsX.items():
		# 	self.pointsX[key] += change[0]
		# for key,val in self.pointsY.items():
		# 	self.pointsY[key] += change[1]
		# Get new positions
		
		# Remove markers
		self.markerRemove()
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

class histogram:
	def __init__(self,plot):
		# Bing the parent plot.
		self.parent = plot
		# A figure instance to plot on.
		self.figure = plt.figure()
		# This is the Canvas Widget that displays the `figure`.
		self.canvas = FigureCanvas(self.figure)
		# Add axes for plotting on.
		self.ax = self.figure.add_axes([0,0,1,1])
		# Redraw.
		self.canvas.draw()
		# Initialise histogram max to zero.
		self.histMax = 0

	def refresh(self):
		# Get maximum value of array for sliders.
		dataMin = np.min(self.parent.data3d)
		dataMax = np.max(self.parent.data3d)
		# Add histogram.
		# bins = 64
		self.histMax,_,_ = self.ax.hist(self.parent.data3d.ravel(),facecolor='k',alpha=0.5,bins=64)
		self.histMax = np.max(self.histMax)
		# Histogram window
		self.ax.plot([dataMin,dataMax],[dataMin,self.histMax],'k-', lw=1)
		self.ax.plot([dataMax,dataMax],[dataMin,self.histMax],'k--', lw=1)
		# Redraw.
		self.canvas.draw()	

	def update(self,minimum,maximum):
		# Remove old window.
		for i in range(len(self.ax.lines)):
			self.ax.lines[0].remove()
		# Add new window.
		self.ax.plot([minimum,maximum],[minimum,self.histMax],'k-', lw=1)
		self.ax.plot([maximum,maximum],[minimum,self.histMax],'k--', lw=1)
		# Redraw.
		self.canvas.draw()

class window:
	def __init__(self,parent,plot,advanced=False):
		# Must pass a parent plot to it (MPL2DFigure).
		self.parent = parent
		self.plot = plot
		self.advanced = advanced
		# Set the size.
		# sizePolicy = QtWidgets.QSizePolicy.Minimum
		# self.parent.setSizePolicy(QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.Minimum)
		# self.parent.setContentsMargins(0,0,0,0)
		self.parent.setMaximumSize(500,170)
		# Get image details from parent.
		self.dataMin = 0
		self.dataMax = 0
		# Create a layout.
		layout = QtWidgets.QFormLayout()
		# Create widgets.
		self.histogram = histogram(plot)
		self.widget = {}
		# Min Slider.
		self.widget['sl_min'] = QtWidgets.QSlider(QtCore.Qt.Horizontal)
		self.widget['sl_min'].setTracking(False)
		self.widget['sl_min'].setEnabled(False)
		# Max Slider.
		self.widget['sl_max'] = QtWidgets.QSlider(QtCore.Qt.Horizontal)
		self.widget['sl_max'].setTracking(False)
		self.widget['sl_max'].setEnabled(False)
		# Labels.
		lb_min = QtWidgets.QLabel('Min')
		lb_max = QtWidgets.QLabel('Max')
		# Connect buttons.
		self.widget['sl_min'].valueChanged.connect(self.updateWindow)
		self.widget['sl_max'].valueChanged.connect(self.updateWindow)
		# Assign layout.
		layout.addRow(self.histogram.canvas)
		layout.addRow(lb_min,self.widget['sl_min'])
		layout.addRow(lb_max,self.widget['sl_max'])
		# Check for advanced options.
		if self.advanced == True:
			# Add radio buttons for 3d arrays where flattening option can be chosen.
			self.widget['rb_sum'] = QtWidgets.QRadioButton('Sum')
			self.widget['rb_max'] = QtWidgets.QRadioButton('Max')
			self.widget['rb_sum'].toggled.connect(self.updateFlatteningMode)
			self.widget['rb_max'].toggled.connect(self.updateFlatteningMode)
			# Defaults.
			self.widget['rb_sum'].setChecked(True)
			self.widget['rb_max'].setChecked(False)
			# Add to layout.
			layout.addRow(self.widget['rb_sum'],self.widget['rb_max'])
		# Set layout.
		self.parent.setLayout(layout)

	def refreshControls(self):
		# Get image details from parent.
		self.dataMin = np.min(self.plot.data3d)
		self.dataMax = np.max(self.plot.data3d)
		# Slider Min Controls
		self.widget['sl_min'].setMinimum(self.dataMin)
		self.widget['sl_min'].setMaximum(self.dataMax-1)
		self.widget['sl_min'].setValue(self.dataMin)
		# Slider Max Controls
		self.widget['sl_max'].setMinimum(self.dataMin+1)
		self.widget['sl_max'].setMaximum(self.dataMax)
		self.widget['sl_max'].setValue(self.dataMax)
		# Enable Sliders
		self.widget['sl_min'].setEnabled(True)
		self.widget['sl_max'].setEnabled(True)
		# Refresh histogram.
		self.histogram.refresh()

	def updateFlatteningMode(self):
		if self.widget['rb_sum'].isChecked() == True:
			mode = 'sum'
		elif self.widget['rb_max'].isChecked() == True:
			mode = 'max'
		self.plot._radiographMode = mode

	def updateWindow(self):
		if self.plot.image == None:
			# If there is no image yet loaded, do nothing.
			return

		# Get minimum and maximum values from sliders.
		minimum = self.widget['sl_min'].value()
		maximum = self.widget['sl_max'].value()
		# Calculate scale.
		scale = (self.dataMax-self.dataMin) / (maximum-minimum)
		# Find shifted maximum.
		# shift = minimum - self.dataMin
		# maximum_shifted = maximum - np.absolute(minimum)
		shift = -minimum
		maximum_shifted = maximum + shift
		# Copy array data.
		self.plot.data = np.array(self.plot.data3d)
		# Shift array.
		self.plot.data += shift
		# Set every negative value to zero.
		# self.plot.data[self.plot.data < self.dataMin] = self.dataMin
		self.plot.data[self.plot.data < 0] = 0
		# Set everything above the maximum value to max.
		self.plot.data[self.plot.data > maximum_shifted] = maximum_shifted
		# Scale data.
		self.plot.data *= scale
		# Shift back to original position.
		self.plot.data += self.dataMin
		# Check for advanced options.
		if self.advanced == True:
			# Check plot number.
			if self.plot.imageIndex == 0:
				direction = 2
			elif self.plot.imageIndex == 1:
				direction = 1
			# Check flattening mode.
			if self.plot._radiographMode == 'max':
				self.plot.data = np.amax(self.plot.data,axis=direction)
			elif self.plot._radiographMode == 'sum':
				self.plot.data = np.sum(self.plot.data,axis=direction)
			else:
				pass
		# Set data.
		self.plot.image.set_data(self.plot.data)
		# Redraw canvas.
		self.plot.canvas.draw()
		# Update histogram overlay.
		self.histogram.update(minimum,maximum)
		# Restrict the value of each slider?? So that one can't go past the other.