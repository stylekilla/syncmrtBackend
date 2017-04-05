import numpy as np
from scipy import ndimage

def optimiseFiducials(pts,data,dims,markersize):
	'''
	Optimise fiducials will take an ROI around a point and re-center it based on the pixel values.
	- Requires points in mm
	- requires dims in mm
	- requires markerSize in mm
	- requires pixel data array
	- gives out points in mm
	- input should be [row,col]; we have made exceptions to align x/y and row/col in here
	'''
	dims = np.flip(dims,0)
	# Create array for optimised points.
	pts_ctrds = np.zeros((np.shape(pts)))

	# Turn point measurements (mm) into integers for indexing.
	pts = pts/dims
	x_roi = int(markersize*3/dims[0])
	y_roi = int(markersize*3/dims[1])

	# Iterate over number of points.
	for i in range(np.shape(pts)[0]):
		# Select the coordinate in the array and sample the value.
		x = int(pts[i,0])
		y = int(pts[i,1])
		clr = data[y,x]

		# Create ROI to look at.
		roi = data[(y-y_roi):(y+y_roi),(x-x_roi):(x+x_roi)]
		roi_cnr = np.array([x-x_roi,y-y_roi])

		# Define thresholds of +/- X% of that value.
		pct = 3
		thresh_max = clr+np.absolute(clr*(pct/100))
		thresh_min = clr-np.absolute(clr*(pct/100))

		# Mask the image.
		roi[(roi<thresh_min)] = 0
		roi[(roi>thresh_max)] = 0
		# Set remaining values to binary 1.
		roi[(roi>0)] = 1

		# Find connection maps of each element.
		labels, index = ndimage.label(roi)

		# Create empty array size of indexes.
		labels_com = np.zeros((index,2))
		# Get center of mass for each element.
		for j in range(index):
			labels_com[j,:] = ndimage.measurements.center_of_mass(roi,labels,j+1)

		# Flip labels_com L to R to order as x,y.
		labels_com = np.fliplr(labels_com)
		labels_com += roi_cnr

		# Find the CoM that most accurately represents a datapoint.
		# Test points.
		test = np.absolute(labels_com-pts[i,:])
		dist = np.zeros((index,1))
		# Find the length of each set of points.
		for j in range(index):
			dist[j,0] = np.sqrt(test[j,0]**2 + test[j,1]**2)
		# Find the smallest line.
		ind = np.argmin(dist)
		# Set the value.
		pts_ctrds[i,:] = labels_com[ind,:]

	# Return pts_ctrds to measurement values (mm).
	pts_ctrds = pts_ctrds*dims
	# Return centroid refined points as np array.
	return pts_ctrds