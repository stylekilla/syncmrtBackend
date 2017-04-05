import matplotlib as mpl
mpl.use('Qt5Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# from skimage import exposure
from skimage.external import tifffile as tiff

class mpl3DFigure:

	def __init__(self,view):
		# Set up empty plot variables.
		self.volume = None
		# self.adjusted = None
		self.dims = None
		self.x = []
		self.y = []
		self.i = 0
		self.max_markers = 0
		self.marker_scat = ()
		# Create a figure to plot on.
		self.fig = plt.figure()
		# Set face color.
		self.fig.patch.set_facecolor('#FFFFFF')
		# Create an axis in the figure.
		self.ax = self.fig.add_subplot(111, axisbg='#FFFFFF')
		# Set tight fitting.
		self.fig.tight_layout()
		# Set the tick colors.
		self.ax.tick_params(colors='#000000')

		if view == 'Coronal':
			self.ax.set_title('0 Degree View')
			self.ax.set_xlabel('X-axis (LR)')
			self.ax.set_ylabel('Z-axis (HF)')
		elif view == 'Sagittal':
			self.ax.set_title('90 Degree View')
			self.ax.set_xlabel('Y-axis (PA)')
			self.ax.set_ylabel('Z-axis (HF)')
		else:
			# Deal with something that shouldn't occur.
			self.ax.set_title('Unknown')
			self.ax.set_xlabel('Unknown')
			self.ax.set_ylabel('Unknown')

		# Set Label Colors.
		self.ax.title.set_color('#000000')
		self.ax.xaxis.label.set_color('#000000')
		self.ax.yaxis.label.set_color('#000000')
		# Create a canvas widget for Qt to use.
		self.canvas = FigureCanvas(self.fig)
		# Refresh the canvas.
		self.canvas.draw()

	def loadImage(self,fn,pix,orientation='HFS',img=1,format='npy'):
		# Try to read in numpy array.
		if format == 'npy':
			self.data = np.load(fn)
		else:
			# For everything else assume it's an image readable by tifffile.
			self.data = tiff.imread(fn)

		# Patient imaging orientation. Calculate the extent (left, right, bottom, top).
		if orientation == 'HFS':
			if img == 1:
				self.dims = np.array([0,np.shape(self.data)[1]*pix[0],np.shape(self.data)[0]*pix[2],0])
			if img == 2:
				self.dims = np.array([0,np.shape(self.data)[1]*pix[1],np.shape(self.data)[0]*pix[2],0])
		elif orientation == 'FHS':
			if img == 1:
				self.dims = np.array([0,np.shape(self.data)[1]*pix[0],np.shape(self.data)[0]*pix[2],0])
			if img == 2:
				self.dims = np.array([0,np.shape(self.data)[1]*pix[1],np.shape(self.data)[0]*pix[2],0])
		# Display the image.
		self.image = self.ax.imshow(self.data, cmap='bone', extent=self.dims)
		self.ax.set_autoscale_on(False)
		# Refresh the canvas.
		self.canvas.draw()
		# Start Callback ID
		self.cid = self.canvas.mpl_connect('button_press_event', self.onClick)
	
	def onClick(self,event):
		# If mouse button 1 is clicked (left click).
		if event.button == 1:
			# Create scatter point and numbered text for each marker up to max markers.
			if self.i < self.max_markers:
				self.x.append(event.xdata)
				self.y.append(event.ydata)
				self.i = self.i+1
				# Create tuple list of scatter and text plots.
				a = self.ax.scatter(event.xdata,event.ydata,c='r',marker='+',s=50)
				b = self.ax.text(event.xdata+1,event.ydata-3,self.i,color='r')
				tmp = a,b
				self.marker_scat = self.marker_scat + tmp
				# Refresh canvas.
				self.canvas.draw()
			else:
				pass

	def resetMarkers(self,args=None):
		# Reset all parameters back to their initial states.
		if args == 'all':
			self.x = []
			self.y = []
			self.i = 0
		# Remove each scatter point from the canvas.
		for i in range(len(self.marker_scat)):
			self.marker_scat[i].remove()
		# Reset the tuple list.
		self.marker_scat = ()
		# Redraw the canvas. 
		self.canvas.draw()

	def updateImage(self,data):
		# Set image data.
		self.image.set_data(data)
		# Refresh the canvas.
		self.canvas.draw()

	def markerUpdate(self):
		# Reset the markers.
		self.resetMarkers()
		# Re-plot markers with pts. 
		for i in range(self.max_markers):
			# Create tuple list of scatter and text plots.
			a = self.ax.scatter(self.x[i],self.y[i],c='b',marker='+',s=50)
			b = self.ax.text(self.x[i]+1,self.y[i]-3,i+1,color='b')
			tmp = a,b
			self.marker_scat = self.marker_scat + tmp
		# Refresh the canvas.
		self.canvas.draw()