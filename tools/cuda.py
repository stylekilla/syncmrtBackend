import pycuda.driver as cuda
import pycuda.gpuarray as gpuarray
import pycuda.autoinit
from pycuda.compiler import SourceModule
import numpy as np
import site
from math import sin, cos

'''
The intention is to start a GPU interface for CUDA with a dataset. 
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

	def rotate(self,y,x,z):
		# Rotate assumings x y z angle input, x and y have been swapped to adjust for col/row.
		# Initialise Kernel
		fp = site.getsitepackages()[0]
		mod = SourceModule(open(fp+"/syncmrt/tools/cudaKernels/image.c", "r").read(),keep=True)
		func = mod.get_function("rotate")

		# Set texture (3D array).
		tex = mod.get_texref("tex")
		tex.set_array(self.gpuTexture)

		# Input elements.
		rotation = np.deg2rad(np.array([x,y,z])).astype(np.float32)
		texShape = np.array(self.arrIn.shape).astype(np.float32)

		# Get 3D rotation vector, R.
		R = np.array([[cos(rotation[1])*cos(rotation[2]), 
			cos(rotation[1])*sin(rotation[2]), 
			-sin(rotation[1])],
			[sin(rotation[0])*sin(rotation[1])*cos(rotation[2])-cos(rotation[0])*sin(rotation[2]), 
			sin(rotation[0])*sin(rotation[1])*sin(rotation[2])+cos(rotation[0])*cos(rotation[2]), 
			sin(rotation[0])*cos(rotation[1])],
			[cos(rotation[0])*sin(rotation[1])*cos(rotation[2])+sin(rotation[0])*sin(rotation[2]), 
			cos(rotation[0])*sin(rotation[1])*sin(rotation[2])-sin(rotation[0])*cos(rotation[2]), 
			cos(rotation[0])*cos(rotation[1])]])

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
		self.arrOut = np.zeros(outShape,dtype=np.float32,order='C')

		# Block and grid size.
		blockDim = (8,8,8)
		bestFit = divmod(np.array(self.arrIn.shape),np.array(blockDim))
		gridDim = (int(bestFit[0][0]+(bestFit[1][0]>0)),
			int(bestFit[0][1]+(bestFit[1][1]>0)),
			int(bestFit[0][2]+(bestFit[1][2]>0)))

		# Call function.
		func(cuda.InOut(self.arrOut),
			rotation[0],rotation[1],rotation[2],
			texShape[0],texShape[1],texShape[2],
			outShape[0],outShape[1],outShape[2],
			block=blockDim,grid=gridDim,
			texrefs=[tex])


		inMax = np.amax(self.arrIn)
		inMin = np.amax(self.arrIn)

		return self.arrOut, newPixelDimensions

	def LUTstuff(self):
		pass

