import pycuda.driver as cuda
import pycuda.gpuarray as gpuarray
import pycuda.autoinit
from pycuda.compiler import SourceModule
import numpy as np
import site
from math import sin, cos
from syncmrt.tools.quaternions import quaternionMath as q

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

	def copyTexture(self,data, pixelSize=None, extent=None, isocenter=None):
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

		self.pixelSize = pixelSize
		self.isocenter = isocenter
		# Extent[l,r,b,t,f,b]
		self.extent = extent
		# Trigger for setting bottom left corner as 0,0,0.
		self.zeroExtent = False

	def rotate(self,x,y,z,order='xyz',x1=None,y1=None,z1=None):
		# Eventually send a list xyz and compute R based on order dynamically...
		# Initialise Kernel
		fp = site.getsitepackages()[0]
		mod = SourceModule(open(fp+"/syncmrt/tools/cudaKernels/rotate3D.c", "r").read(),keep=True)

		# Default axes.
		xaxis = np.array(([1,0,0]))
		yaxis = np.array(([0,1,0]))
		zaxis = np.array(([0,0,1]))

		if order == 'pat-gant-col':
			# All angles should go in opposite direction to DICOM standard.
			# z 	patient support angle
			# x 	gantry angle
			# z1 	collimator angle

			rz = q.rotation(z,axis=zaxis)
			# rx = q.rotation(x,axis=xaxis)
			# rxi = q.inverse(rx)
			# tempaxis = q.quaternion(zaxis)
			# newaxis = q.product(q.product(rx,tempaxis),rxi)
			# newaxis = np.absolute(newaxis)
			# rz1 = q.rotation(z1,axis=newaxis[1:])

			# print('newaxis')
			# print(newaxis)

			# world = q.product(rx,rz)
			# rotation = q.product(world,rz1)
			
			rzi = q.inverse(rz)
			rz1 = q.rotation(z+z1,axis=zaxis)
			tempaxis = q.quaternion(xaxis)
			newaxis = q.product(q.product(rz,tempaxis),rzi)
			print('newaxis')
			print(newaxis)
			rx = q.rotation(x,axis=newaxis[1:])
			rotation = q.product(rz1,rx)

			R = q.euler(rotation)

			print('rotation')
			print(R)
			print('')

		else:
			# Assume xyz.
			rx = q.rotation(x,axis=xaxis)
			ry = q.rotation(y,axis=yaxis)
			rz = q.rotation(z,axis=zaxis)

			rotation = q.product(q.product(rx,ry),rz)
			R = q.euler(rotation)

		# Force float32 before we send to c.
		R = np.float32(R)

		# Load the *.c function.
		func = mod.get_function("rotate")

		# Set texture (3D array).
		tex = mod.get_texref("tex")
		tex.set_array(self.gpuTexture)

		# Input elements.
		texShape = np.array(self.arrIn.shape).astype(np.float32)

		# Get outshape by taking bounding box of vertice points.
		vert000 = np.array([0,0,0])
		vert100 = np.dot(np.array((texShape[0],0,0)),R)
		vert010 = np.dot(np.array((0,texShape[1],0)),R)
		vert110 = np.dot(np.array((texShape[0],texShape[1],0)),R)
		vert001 = np.dot(np.array((0,0,texShape[2])),R)
		vert101 = np.dot(np.array((texShape[0],0,texShape[2])),R)
		vert011 = np.dot(np.array((0,texShape[1],texShape[2])),R)
		vert111 = np.dot(texShape,R)
		vertices = np.vstack([vert000,vert100,vert010,vert110,vert001,vert101,vert011,vert111])

		# Find minimum and maximum vertice points.
		minimum = np.amin(vertices,axis=0)
		maximum = np.amax(vertices,axis=0)
		# Find the difference between the two as a whole number.
		shape = maximum-minimum
		outShape = np.rint(shape).astype(np.int32)
		# Set shape (as float32 for cuda)
		self.arrOut = np.zeros(outShape,dtype=np.float32,order='C')

		# Block and grid size.
		blockDim = (8,8,8)
		bestFit = divmod(np.array(self.arrIn.shape),np.array(blockDim))
		gridDim = (int(bestFit[0][0]+(bestFit[1][0]>0)),
			int(bestFit[0][1]+(bestFit[1][1]>0)),
			int(bestFit[0][2]+(bestFit[1][2]>0)))

		# Call cuda kernel with inputs/outputs.
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

		# Find new isocenter.
		if (not(self.isocenter is None)):
			self.isocenter = np.dot(self.isocenter,R)

		# Find new extent.
		if (not(self.pixelSize is None)) & (not(self.extent is None)):			
			# Row col depth is YXZ.
			row,col,depth = self.arrOut.shape

			# New extent vertices.
			v000 = np.dot(np.array([self.extent[2],self.extent[0],self.extent[4]]),R)
			v001 = np.dot(np.array([self.extent[2],self.extent[0],self.extent[5]]),R)
			v010 = np.dot(np.array([self.extent[3],self.extent[0],self.extent[4]]),R)
			v011 = np.dot(np.array([self.extent[3],self.extent[0],self.extent[5]]),R)
			v100 = np.dot(np.array([self.extent[2],self.extent[1],self.extent[4]]),R)
			v101 = np.dot(np.array([self.extent[2],self.extent[1],self.extent[5]]),R)
			v110 = np.dot(np.array([self.extent[3],self.extent[1],self.extent[4]]),R)
			v111 = np.dot(np.array([self.extent[3],self.extent[1],self.extent[5]]),R)
			vertices = np.vstack([v000,v001,v010,v011,v100,v101,v110,v111])

			# New extent vertices.
			o000 = np.dot(np.array([-1,-1,-1]),R)
			o001 = np.dot(np.array([-1,-1, 1]),R)
			o010 = np.dot(np.array([ 1,-1,-1]),R)
			o011 = np.dot(np.array([ 1,-1, 1]),R)
			o100 = np.dot(np.array([-1, 1,-1]),R)
			o101 = np.dot(np.array([-1, 1, 1]),R)
			o110 = np.dot(np.array([ 1, 1,-1]),R)
			o111 = np.dot(np.array([ 1, 1, 1]),R)
			orientation = np.vstack([o000,o001,o010,o011,o100,o101,o110,o111])

			minimum = np.argmin(orientation,axis=0)
			maximum = np.argmax(orientation,axis=0)

			blf = np.array([vertices[minimum[0],0],
				vertices[minimum[1],1],
				vertices[minimum[2],2]
				])

			trb = np.array([vertices[maximum[0],0],
				vertices[maximum[1],1],
				vertices[maximum[2],2]
				])

			# New extent (l,r,b,t,f,b).
			extent = np.array([
				blf[1],	trb[1],
				blf[0],	trb[0],
				blf[2],	trb[2]
				])

			# print('Params')
			# print(vertices)
			# print(orientation)
			# print(minimum)
			# print(maximum)
			# print(blf)
			# print(trb)
			# print('')

		 # Send back array out, extent.
		return self.arrOut, extent