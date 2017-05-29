import pycuda.driver as cuda
import pycuda.gpuarray as gpuarray
import pycuda.autoinit
from pycuda.compiler import SourceModule
import numpy as np
import site
from math import sin, cos

'''
Starts a GPU interface that we can run kernels from.
	copyTexture(data,dimensions)			Copies data over the GPU for processing. This is copied as a texture which can be referenced.
	rotate(x,y,z,order='xyz',others...)		X controls vertical axis rotation, Y controls horizontal axis rotation, Z controls into page axis rotation.
'''

class gpuInterface:
	def __init__(self):
		self.arrIn = None
		self.arrOut = None

		'''
		Do a device check?
		'''

	def copyTexture(self,data, patientPosition=None, pixelSize=None, extent=None, isocenter=None):
		# Convert data to float32 array in Contiguous ordering.
		self.arrIn = np.array(data,dtype=np.float32,order='C')
		d,h,w = self.arrIn.shape

		descr = cuda.ArrayDescriptor3D()
		descr.width = w
		descr.height = h
		descr.depth = d
		descr.format = cuda.dtype_to_array_format(self.arrIn.dtype)
		descr.num_channels = 1
		# descr.flags = 0
		self.gpuTexture = cuda.Array(descr)

		# Copy array data across. This puts a 3D array in linear memory on the GPU.
		copy = cuda.Memcpy3D()
		copy.set_src_host(self.arrIn)
		copy.set_dst_array(self.gpuTexture)
		copy.src_pitch = self.arrIn.strides[1]
		copy.width_in_bytes = self.arrIn.strides[1]
		copy.height = h
		copy.depth = d
		copy.src_height = h
		copy()

		self.patientPosition = np.array(patientPosition)
		self.pixelSize = pixelSize
		self.isocenter = isocenter
		# 3D extent, not 2D.
		self.extent = extent

	def rotate(self,x,y,z,order='xyz',x1=None,y1=None,z1=None):
		# Eventually send a list xyz and compute R based on order dynamically...

		# Initialise Kernel
		fp = site.getsitepackages()[0]
		mod = SourceModule(open(fp+"/syncmrt/tools/cudaKernels/rotate3D.c", "r").read(),keep=True)

		# Convert x,y,z to float32 radians.
		x = np.deg2rad(x).astype(np.float32)
		y = np.deg2rad(y).astype(np.float32)
		z = np.deg2rad(z).astype(np.float32)

		# Calculate rotation vectors.
		Rx = np.array([
			[1, 0, 0],
			[0, cos(x),-sin(x)],
			[0, sin(x), cos(x)]
			])
		Ry = np.array([
			[ cos(y), 0, sin(y)],
			[0, 1, 0],
			[-sin(y), 0, cos(y)]
			])
		Rz = np.array([
			[ cos(z),-sin(z), 0],
			[ sin(z), cos(z), 0],
			[0, 0, 1]
			])

		# If second axis rotations are required, compute their rotation vectors here.
		if x1 != None:
			x1 = np.deg2rad(x1).astype(np.float32)
			Rx1 = np.array([
				[1, 0, 0],
				[0, cos(x1),-sin(x1)],
				[0, sin(x1), cos(x1)]
				])
		if y1 != None:
			y1 = np.deg2rad(y1).astype(np.float32)
			Ry1 = np.array([
				[ cos(y1), 0, sin(y1)],
				[0, 1, 0],
				[-sin(y1), 0, cos(y1)]
				])
		if z1 != None:
			z1 = np.deg2rad(z1).astype(np.float32)
			Rz1 = np.array([
				[ cos(z1),-sin(z1), 0],
				[ sin(z1), cos(z1), 0],
				[0, 0, 1]
				])

		# Calculate final rotation vector as per order of application of rotations.
		if order=='yzx':
			R = Ry @ Rz @ Rx
		elif order=='yzy':
			R = Ry @ Rz @ Ry1
		elif order=='zxz':
			R = Rz @ Rx @ Rz1
		elif order=='zyz':
			R = Rz @ Ry @ Rz1
		elif order=='zxzx':
			R = Rz @ Rx @ Rz1 @ Rx1
		else:
			# Default to XYZ order.
			R = Rx @ Ry @ Rz

		# Force float32 before we send to c.
		R = np.float32(R)

		# Calculate new axes.
		# position = np.dot(R,self.patientPosition)

		# Load the *.c function.
		func = mod.get_function("rotate")

		# Set texture (3D array).
		tex = mod.get_texref("tex")
		tex.set_array(self.gpuTexture)

		# Input elements.
		texShape = np.array(self.arrIn.shape).astype(np.float32)

		# Get outshape by taking bounding box of maximum vertice points.
		vert100 = np.absolute(np.dot(R, np.array((texShape[0],0,0)).T ))
		vert010 = np.absolute(np.dot(R, np.array((0,texShape[1],0)).T ))
		vert110 = np.absolute(np.dot(R, np.array((texShape[0],texShape[1],0)).T ))
		vert001 = np.absolute(np.dot(R, np.array((0,0,texShape[2])).T ))
		vert101 = np.absolute(np.dot(R, np.array((texShape[0],0,texShape[2])).T ))
		vert011 = np.absolute(np.dot(R, np.array((0,texShape[1],texShape[2])).T ))
		vert111 = np.absolute(np.dot(R, texShape.T ))
		vert = np.vstack([vert100,vert010,vert110,vert001,vert101,vert011,vert111])
		vert = np.amax(vert,axis=0)

		outShape = np.rint(vert).astype(np.int32)

		self.arrOut = np.zeros(outShape,dtype=np.float32,order='C')

		# Block and grid size.
		blockDim = (8,8,8)
		bestFit = divmod(np.array(self.arrIn.shape),np.array(blockDim))
		gridDim = (int(bestFit[0][0]+(bestFit[1][0]>0)),
			int(bestFit[0][1]+(bestFit[1][1]>0)),
			int(bestFit[0][2]+(bestFit[1][2]>0)))

		func(cuda.InOut(self.arrOut),
			R[0][0],
			R[0][1],
			R[0][2],
			R[1][0],
			R[1][1],
			R[1][2],
			R[2][0],
			R[2][1],
			R[2][2],
			texShape[0],texShape[1],texShape[2],
			outShape[0],outShape[1],outShape[2],
			block=blockDim,grid=gridDim,
			texrefs=[tex])

		# Find new extent with respect to isocenter.
		if (not(self.isocenter is None)) & (not(self.pixelSize is None)) & (not(self.extent is None)):
			# Rotate isoc to match output shape geometry.
			isocenter = np.dot(R,self.isocenter)
			pixelSize = np.dot(R,self.pixelSize)
			row,col,depth = self.arrOut.shape
			x,y,z = pixelSize

			extent = np.array([0,col*x,0,row*y,0,depth*z])			

		if (not(self.pixelSize is None)) & (not(self.extent is None)):
			pixelSize = np.dot(R,self.pixelSize)
			row,col,depth = self.arrOut.shape
			x,y,z = pixelSize
			extent = np.array([0,col*x,0,row*y,0,depth*z])


		 # Send back array out, extent of axes [x1,x2,y1,y2,z1,z2]
		return self.arrOut, extent