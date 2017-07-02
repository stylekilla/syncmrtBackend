import matplotlib as mpl
mpl.use('Qt5Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5 import QtGui, QtCore
from syncmrt.imageGuidance import optimiseFiducials

# from skimage import exposure
from skimage.external import tifffile as tiff

class mpl2DFigure:
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
		self.isocenter = [0,0]

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

	def imageLoad(self,fn,extent=np.array([-1,1,-1,1]),imageOrientation='',imageIndex=0):
		'''imageLoad: Load numpy file in, convert to 2D. Connect callbacks and plot.'''		
		self.imageIndex = imageIndex
		self.data3d = np.load(fn)
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

		# Rescale 2d image between 0 and 65535 (16bit)
		self.imageNormalise()
			
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

		self.image = self.ax.imshow(self.data2d, cmap='bone', extent=self.extent)
		self.ax.set_xlim(extent[0:2])
		self.ax.set_ylim(extent[2:4])
		self.ax.set_aspect("equal", "datalim")
		self.canvas.draw()
		# Start Callback ID
		self.cid = self.canvas.mpl_connect('button_press_event', self.eventFilter)

	def imageWindow(self,windows):
		'''Mask 3D array, flatten and redraw 2D array. windows as List of Lists(upper and lower limit)'''
		conditions = ''
		for window in windows:
			conditions += '((self.data3d>'+str(window[0])+')&(self.data3d<'+str(window[1])+'))|'
		conditions = conditions[:-1]
		mask = eval(conditions)
		self.data2d = self.data3d*mask

		if self.imageIndex == 0:
			direction = 2
		elif self.imageIndex == 1:
			direction = 1
			
		if self._radiographMode == 'max':
			self.data2d = np.amax(self.data2d,axis=direction)
		elif self._radiographMode == 'sum':
			self.data2d = np.sum(self.data2d,axis=direction)
		else:
			pass

		# Rescale 2d image between 0 and 65535 (16bit)
		print('Normalise in image window.')
		self.imageNormalise()
		self.image.set_data(self.data2d)
		self.image.set_clim(vmin=self.data2d.min())
		self.image.set_clim(vmax=self.data2d.max())
		self.canvas.draw()

	def imageNormalise(self,lower=0,upper=65535):
		# I seem to be getting vals below 0 after normalisation??? Why?

		# 16-bit image: 65536 levels.
		maximum = np.amax(self.data2d)
		# Find second smallest number (assuming smallest is now zero due to earlier masking).
		minimum = np.unique(self.data2d)[1]
		scale = (upper-lower)/np.absolute(maximum-minimum)
		self.data2d[self.data2d == 0] = minimum
		self.data2d = (self.data2d - minimum)*scale

		print('scale:',scale)
		print('data2d shape:',self.data2d.shape)
		print('data2d min:',self.data2d.min())
		print('data2d max:',self.data2d.max())

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
		points = optimiseFiducials(pointsIn,self.data2d,extent,fiducialSize,threshold)
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

	def overlayIsocenter(self,state=False):
		if state is True:
			# Plot overlay lines.
			self.overlay['isocenterh'] = self.ax.axhline(self.isocenter[1],c='r',alpha=0.5)
			self.overlay['isocenterv'] = self.ax.axvline(self.isocenter[0],c='r',alpha=0.5)

		else:
			# Remove overlay lines.
			self.overlay['isocenterh'].remove()
			self.overlay['isocenterv'].remove()

		self.canvas.draw()

	def eventFilter(self,event):
		# If mouse button 1 is clicked (left click).
		if (event.button == 1) & (self.canvas._pickerActive):
			self.markerAdd(event.xdata,event.ydata)