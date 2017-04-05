import pycuda.driver as cuda
import pycuda.autoinit
from pycuda.compiler import SourceModule
import numpy as np
from math import sin,cos

def rotate(arr,ax='x',deg=0):
	'''
	Find rotation of an array.

	arr: 3D numpy array.
	ax: Axes to rotate around (x, y or z).
	deg: The degrees to rotate by.
	'''
	arr = np.array(arr).astype('float32')
	# Calculate trig funcs of angle. 
	cos_theta = cos(deg)
	sin_theta = sin(deg)
	# Rotation matrix for three cases:
	if ax=='x':
		R = np.array([[1,0,0],
			[0,cos_theta,sin_theta],
			[0,-sin_theta,cos_theta]])
	if ax=='y':
		R = np.array([[cos_theta,0,-sin_theta],
			[0,1,0],
			[sin_theta,0,cos_theta]])
	if ax=='z':
		R = np.array([[cos_theta,sin_theta,0],
			[-sin_theta,cos_theta,0],
			[0,0,1]])
	# Apply rotations.
	arr_rotated = R*arr

def make_rotation_transformation(angle, origin=(0, 0)):
    cos_theta, sin_theta = cos(angle), sin(angle)
    x0, y0 = origin
    def xform(point):
        x, y = point[0] - x0, point[1] - y0
        return (x * cos_theta - y * sin_theta + x0,
                x * sin_theta + y * cos_theta + y0)
    return xform

def rotate(self, angle, anchor=(0, 0)):
    xform = make_rotation_transformation(angle, anchor)
    self._offsets = [xform(v) for v in self._offsets]
