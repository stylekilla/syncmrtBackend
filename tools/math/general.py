import numpy as np

# Currently this is only specific to the MRT stage in Hutch 2B.
def relativeTranslation(rotation,translation):
	''' Rotation should be in degrees. Translation should be 'synchrotron' [x,y].'''
	out = np.array([0,0])

	# Point In. Accounts for H1/H2 motor directions and Synchrotron CS directions.
	x,y = translation
	pIn = np.array([-y,x])

	# Angle, theta, in radians.
	theta = np.deg2rad(rotation)

	# 2D rotation matrix.
	R = np.array([[np.cos(theta),np.sin(theta)],[-np.sin(theta),np.cos(theta)]])

	# Apply rotation matrix (rotates x-y coordinate frame).
	pOut = np.dot(R,pIn)

	# Get output values.
	H1,H2 = pOut

	return H1,H2