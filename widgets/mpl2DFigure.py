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

	# def __init__(self):
	def __init__(self,model):
		self.logMessage = ()
		self.logRank = ()
		self.image = None
		# self.adjusted = None
		self.plotDimensions = None
		self.pointsX = []
		self.pointsY = []
		self.i = 0
		self.markersMaximum = 0
		self.markersList = []
		self.markerModel = model

		self.fig = plt.figure()
		self.fig.patch.set_facecolor('#FFFFFF')
		self.ax = self.fig.add_subplot(111, axisbg='#FFFFFF')
		self.fig.tight_layout()
		self.ax.tick_params(colors='#000000')
		self.ax.title.set_color('#000000')
		self.ax.xaxis.label.set_color('#000000')
		self.ax.yaxis.label.set_color('#000000')

		# Create a canvas widget for Qt to use.
		self.canvas = FigureCanvas(self.fig)
		# Refresh the canvas.
		self.canvas.draw()

		self.canvas._pickerActive = False

	def imageLoad(self,fn,pixelSize,imageOrientation='HFS',imageIndex=1):
		'''Load numpy file in, convert to 2D. Connect callbacks and plot.'''		
		self.data3d = np.load(fn)
		if len(self.data3d.shape) == 3:
			self.data2d = np.sum(self.data3d,axis=2)
			self.pixelSize = pixelSize[0:2]
		else:
			self.data2d = np.array(self.data3d)
			self.pixelSize = pixelSize

		# Image extent (dimensions - Left Right Bottom Top).
		self.plotDimensions = np.array([0, np.shape(self.data2d)[1]*self.pixelSize[1], np.shape(self.data2d)[0]*self.pixelSize[0], 0])

		if imageOrientation == 'HFS':
			if imageIndex == 1:
				self.ax.set_title('HFS')
			if imageIndex == 2:
				self.ax.set_title('HFS2 lol?')
		elif imageOrientation == 'FHS':
			if imageIndex == 1:
				self.ax.set_title('FHS')
			if imageIndex == 2:
				self.ax.set_title('FHS2 lol?')
		else:
			if imageIndex == 1:
				self.ax.set_title('Unknown')
				self.ax.set_xlabel('Unknown')
				self.ax.set_ylabel('Unknown')
			if imageIndex == 2:
				self.ax.set_title('Unknown')
				self.ax.set_xlabel('Unknown')
				self.ax.set_ylabel('Unknown')

		self.image = self.ax.imshow(self.data2d, cmap='bone', extent=self.plotDimensions)
		self.ax.set_autoscale_on(False)
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
		self.data2d = np.sum(self.data2d,axis=2)
		self.image.set_data(self.data2d)
		self.image.set_clim(vmin=self.data2d.min())
		self.image.set_clim(vmax=self.data2d.max())
		self.canvas.draw()

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
						print('Keys: ', key*2, key*2+1)
						print(self.markersList)
						self.canvas.draw()
						# Update pointsXY lists.
						self.pointsX[key] = x
						self.pointsY[key] = y

	def markerRemove(self,marker=-1):
		'''Clear the specified marker. Else clear all markers.'''
		self.i = 0
		self.pointsX = []
		self.pointsY = []
		for index in range(len(self.markersList)):
			self.markersList[index].remove()
		self.markersList = []
		self.markerModel.clearMarkers(self.markersMaximum)
		self.canvas.draw()

	def markerOptimise(self,fiducialSize):
		'''Call syncMRT optimise points module. Send points,data,dims,markersize.'''
		pointsIn = np.column_stack((self.pointsX,self.pointsY))

		points = optimiseFiducials(pointsIn,self.data2d,self.pixelSize,fiducialSize)
		self.pointsXoptimised = points[:,0]
		self.pointsYoptimised = points[:,1]

		# Re-plot with optimised points over the top (in blue).
		self.markerListOptimsed = []
		for i in range(len(self.pointsXoptimised)):
			x = self.pointsXoptimised[i]
			y = self.pointsYoptimised[i]
			# Plot marker list.
			scatter = self.ax.scatter(x,y,c='b',marker='+',s=50)
			text = self.ax.text(x+1,y-3,i+1,color='b')
			self.markerListOptimsed += scatter,text

		self.canvas.draw()

	def eventFilter(self,event):
		# If mouse button 1 is clicked (left click).
		if (event.button == 1) & (self.canvas._pickerActive):
			self.markerAdd(event.xdata,event.ydata)