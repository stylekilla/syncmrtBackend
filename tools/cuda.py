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

	def copyTexture(self,data, dimensions):
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

		self.pixelDimensions = np.array(dimensions)

	def rotate(self,x,y,z,order='xyz',x1=None,y1=None,z1=None):
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
			func = mod.get_function("rotateYZX")
			R = np.dot(Ry,Rz,Rx)
		if order=='yzy':
			func = mod.get_function("rotateYZY")
			R = np.dot(Ry,Rz,Ry1)
			# x is not being used so replace that with y1.
			x = y1
		if order=='zxz':
			func = mod.get_function("rotateZXZ")
			R = np.dot(Rz,Rx,Rz1)
			# y is not being used so replace that with z1.
			y = z1
		else:
			# Default to XYZ order.
			func = mod.get_function("rotateXYZ")
			R = np.dot(Rx,Ry,Rz)

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

		newPixelDimensions = np.absolute(np.dot(R,self.pixelDimensions.reshape(3,1))).T[0]
		print('pixelDimensions',self.pixelDimensions)
		print('newPixelDimensions',newPixelDimensions)
		self.arrOut = np.zeros(outShape,dtype=np.float32,order='C')

		# Block and grid size.
		blockDim = (8,8,8)
		bestFit = divmod(np.array(self.arrIn.shape),np.array(blockDim))
		gridDim = (int(bestFit[0][0]+(bestFit[1][0]>0)),
			int(bestFit[0][1]+(bestFit[1][1]>0)),
			int(bestFit[0][2]+(bestFit[1][2]>0)))

		# Call cuda function.
		func(cuda.InOut(self.arrOut),
			x,y,z,
			texShape[0],texShape[1],texShape[2],
			outShape[0],outShape[1],outShape[2],
			block=blockDim,grid=gridDim,
			texrefs=[tex])

		return self.arrOut, newPixelDimensions