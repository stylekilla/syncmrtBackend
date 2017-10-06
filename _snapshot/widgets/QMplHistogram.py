import matplotlib as mpl
mpl.use('Qt5Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5 import QtGui, QtCore
from syncmrt.imageGuidance import optimiseFiducials

class histogram:
	'''
	Documentation for now:
	- imageLoad(filename, pixelsize, oreitnation, imagenumber(/2), fileformat): Load image into canvas.
	- imageUpdate(newdata): Send new data to canvas.
	- markerUpdate(): Called from eventFilter (cid: callbackID), appends new markers?
	- markerReset(markerspecifier): Resets the markers (either one or all).
	- eventFilter(event): Based on the event identifier we can tell it to do something.
	'''

	def __init__(self,data):

		plt.hist(lum_img.ravel(), bins=256, range=(0.0, 1.0), fc='k', ec='k')