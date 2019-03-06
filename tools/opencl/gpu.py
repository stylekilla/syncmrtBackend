import pyopencl as cl
import numpy as np

'''
This uses OpenCL for GPU parallel methods.
Written ocl kernels are stored in ./kernels.
Workflow is:
	1. Initialise GPU class
	2. Copy data to device to be used
	3. Run a kernel on that data
	4. Recieve an output
'''

class gpu:
	def __init__(self):
		'''
		1. Initialise some parameters
		2. Find a suitable device
		3. Create a context and queue for work to take place in
		'''
		# Some class members.
		self.pixelSize = None
		self.isocenter = None
		self.extent = None
		self.zeroExtent = False

		# Find avail devices.
		platforms = cl.get_platforms()
		cpuList = []
		gpuList = []
		for plt in platforms:
			cpuList += plt.get_devices(cl.device_type.CPU)
			gpuList += plt.get_devices(cl.device_type.GPU)
		# Create a device context.
		try:
			self.ctx = cl.Context(devices=[gpuList[0]])
		except:
			self.ctx = cl.Context(devices=[cpuList[0]])
			
		# Create a device queue.
		self.queue = cl.CommandQueue(self.ctx)

	def rotate(self,data,rotations=[],pixelSize=None,extent=None,isocenter=None):
		'''
		Here we give the data to be copied to the GPU and give some deacriptors about the data.
		We must enforce datatypes as we are dealing with c and memory access/copies.
		Rotations happen about real world (x,y,z) axes.
		'''
		# Read in array and force the datatype for the gpu.
		arrIn = np.array(data,order='C').astype(np.int32)

		# Get rotation matrices (one for GPU and one for Python, they operate differently)!
		rotations,gpuRotations = self.generateRotationMatrix(rotations)

		# Create a basic box for calculations of a cube. Built off (row,cols,depth).
		basicBox = np.array([
			[0,0,0],
			[0,1,0],
			[1,0,0],
			[1,1,0],
			[0,0,1],
			[0,1,1],
			[1,0,1],
			[1,1,1]])

		# Input array shape
		inputShape =  basicBox*arrIn.shape

		# Output array shape after rotation.
		outputShape = np.empty((8,3),dtype=int)
		for i in range(8):
			outputShape[i,:] = gpuRotations@inputShape[i,:]
		mins = np.absolute(np.amin(outputShape,axis=0))
		maxs = np.absolute(np.amax(outputShape,axis=0))
		outputShape = np.rint(mins+maxs).astype(int)

		# print('In Shape',arrIn.shape)
		# print('Out Shape',outputShape)

		# Create empty output array set to -1000.
		arrOut = np.zeros(outputShape).astype(np.int32)-1000
		arrOutShape = np.array(arrOut.shape).astype(np.int32)

		'''
		The GPU wizardry:
			- First we do the data transfer from host to device.
			- Then we run the program.
			- Then we get the results.
		'''

		# Create memory flags.
		mf = cl.mem_flags
		# GPU buffers.
		gpuIn = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=arrIn)
		gpuRotation = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=gpuRotations)
		gpuOut = cl.Buffer(self.ctx, mf.WRITE_ONLY | mf.COPY_HOST_PTR, hostbuf=arrOut)
		gpuOutShape = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=arrOutShape)

		# Get kernel source.
		import inspect,os
		fp = os.path.dirname(inspect.getfile(gpu))
		sourceKernel = open(fp+"/kernels/rotate.cl", "r").read()		
		# Compile kernel.
		program = cl.Program(self.ctx,sourceKernel).build()
		# Kwargs
		kwargs = (gpuIn,
			gpuRotation,
			gpuOut,
			gpuOutShape
			)
		# Run the program.
		program.rotate3d(self.queue,arrIn.shape,None,*(kwargs))

		# Get results
		cl.enqueue_copy(self.queue, arrOut, gpuOut)

		# Remove any dirty array values in the output.
		arrOut = np.nan_to_num(arrOut)

		# Get axes directions.
		axes = np.sign(pixelSize).astype(int)

		# Get dicom origin offset from middle of array.
		extentLength = np.absolute(extent)
		offset_x = extent[0] + axes[0]*(extentLength[0]+extentLength[1])/2
		offset_y = extent[2] + axes[1]*(extentLength[2]+extentLength[3])/2
		offset_z = extent[4] + axes[2]*(extentLength[4]+extentLength[5])/2
		offset = np.array([offset_x,offset_y,offset_z])

		# print('Extent:',extent)
		# print('Extent Length:',extentLength)
		# print('Axes direction:',axes)
		# print('Offset:',offset)

		# Rotate the pixelSize if specified.
		if pixelSize is not None: 
			# Apply the rotations.
			# print('pixel input:',pixelSize)
			self.pixelSize = rotations@pixelSize
			# print('pixel rotated:',self.pixelSize)

		# Rotate the isocenter if specified.
		if isocenter is not None: 
			# Apply the rotations.
			# print('isocenter input:',isocenter)
			self.isocenter = (rotations@isocenter)*np.sign(self.pixelSize).astype(int)
			# self.isocenter = self.rotateWithOffset(isocenter,rotations,offset)*np.sign(self.pixelSize).astype(int)
			# self.isocenter = np.array([isocenter[pyAxes[0]], isocenter[pyAxes[1]], isocenter[pyAxes[2]]])
			# print('isocenter rotated:',self.isocenter)

		if extent is not None: 
			# Make the 8 corners of the bounding box as (y,x,z) coordinates for python.
			basicBox = np.array([
				[0,0,0],
				[1,0,0],
				[0,1,0],
				[1,1,0],
				[0,0,1],
				[1,0,1],
				[0,1,1],
				[1,1,1]]).astype(np.float64)

			inputExtent = np.array([
				[extent[0],extent[2],extent[4]],
				[extent[1],extent[2],extent[4]],
				[extent[0],extent[3],extent[4]],
				[extent[1],extent[3],extent[4]],
				[extent[0],extent[2],extent[5]],
				[extent[1],extent[2],extent[5]],
				[extent[0],extent[3],extent[5]],
				[extent[1],extent[3],extent[5]]]).astype(np.float64)

			# 1. Setup bounding box to match axes directions.
			basicBox *= np.sign(pixelSize)
			# 1.1 Find minimums and maximums of 
			# 1.1.1 the bounding box.
			boxMin = np.min(basicBox,axis=0)
			boxMax = np.max(basicBox,axis=0)
			# 1.1.2 the extent box.
			extentMin = np.min(inputExtent,axis=0)
			extentMax = np.max(inputExtent,axis=0)	

			# print('Basic Box Axes Ordered')
			# print(basicBox)

			# 1.2 Create input list of box corners in mm.
			inputExtent = np.zeros(basicBox.shape)

			# 1.3 Place mm values based on box corners.
			for i in range(3):
				if pixelSize[i] < 0:
					# Negative axes direction: take maximums to minimums.
					inputExtent[:,i] += (basicBox==boxMin[i])[:,i]*extentMax[i]
					inputExtent[:,i] += (basicBox==boxMax[i])[:,i]*extentMin[i]
				else:
					# Positive direction.
					inputExtent[:,i] += (basicBox==boxMin[i])[:,i]*extentMin[i]
					inputExtent[:,i] += (basicBox==boxMax[i])[:,i]*extentMax[i]

			# print('Input Extent')
			# print(inputExtent)

			# 2.1.1 Make another 8 corner array to rotate the basic box and see the outcome.
			basicBoxTest = np.empty(inputExtent.shape)
			# 2.1.2 Make an output extent.
			outputExtent = np.array(inputExtent)
			# 2.1.3 Center input extent.
			extentOffset = extentMin + ( (extentMax-extentMin)/2 )
			# print('extentOffset',extentOffset)
			# Take extent offset away from input extent.
			inputExtent -= extentOffset
			# Rotate extent offset.
			extentOffset = np.absolute(rotations)@extentOffset
			# print('rotated extent offset',extentOffset)

			# 2.2 Rotate the basicBox and outputExtent.
			for i in range(8):
				basicBoxTest[i,:] = rotations@basicBox[i,:]
				# point = np.hstack([inputExtent[i,:],1])
				outputExtent[i,:] = rotations@inputExtent[i,:]
				# outputExtent[i,:] = np.absolute(rotations)@inputExtent[i,:]
				# outputExtent[i,:] = self.rotateWithOffset(outputExtent[i,:],np.absolute(rotations),offset)
			
			# TESTING TESTING TESTING
			# outputExtent = np.absolute(outputExtent)
			# Add back the rotated offset.
			outputExtent += extentOffset

			# print('BasicBox Rotated Test')
			# print(basicBoxTest)				
			# print('Output Extent')
			# print(outputExtent)

			# 2.3 Find the minimum point in each direction of the basic box test.
			# minimumPoints = np.argmin(basicBoxTest,axis=0)
			# maximumPoints = np.argmax(basicBoxTest,axis=0)
			minimumPoints = np.min(outputExtent,axis=0)
			maximumPoints = np.max(outputExtent,axis=0)

			# print('minimumPoints:',minimumPoints)
			# print('maximumPoints:',maximumPoints)

			# Add 1 to output shape for extent (one extra pixel involved).
			# outputShape += 1

			self.extent = np.zeros(6)

			# 2.4 Place mm values based on box corners.
			for i in range(3):
				if self.pixelSize[i] < 0:
					# Negative axes direction: take maximums to minimums.
					self.extent[i*2] += maximumPoints[i]
					self.extent[i*2+1] += minimumPoints[i]
				else:
					# Positive direction.
					self.extent[i*2] += minimumPoints[i]
					self.extent[i*2+1] += maximumPoints[i]
			# x1 = outputExtent[minimumPoints[0],0]
			# x2 = outputExtent[maximumPoints[0],0]
			# y1 = outputExtent[minimumPoints[1],1]
			# y2 = outputExtent[maximumPoints[1],1]
			# z1 = outputExtent[minimumPoints[2],2]
			# z2 = outputExtent[maximumPoints[2],2]

			# Compile values into extent.
			# self.extent = np.array([x1,x2,y1,y2,z1,z2])

			# print('In Extent',extent)
			# print('Out Extent',self.extent)

		# Trigger for setting bottom left corner as 0,0,0. WHAT EVEN IS THIS???
		self.zeroExtent = False

		return arrOut

	def generateRotationMatrix(self,rotationList):

		'''
		Generate a 3x3 rotation matrix.
		Here we make the following assumptions:
			- Axes are 0/1/2 which match real world x/y/z which match python y/x/z (as python is row-major).
			- Inputs are a list of strings in the format of: 
				- '190' means take the first axis, '1' and rotate '90' degrees about it.
				- '0-90' means take the first axis, '0' and rotate '-90' degrees about it.
		'''
		# Begin with identity matrix.
		pymat = np.identity(3)
		gpumat = np.identity(3)
		# Iterate through desired rotations.
		# CW IS NEGATIVE 
		# CCW IS POSITIVE (AS PER TRIG CIRCLE)
		for i in range(len(rotationList)):
			axis = int(rotationList[i][0])
			value = np.deg2rad(float(rotationList[i][1:]))
			if axis == 0:
				# Rotation about real world x.
				py = np.array([[1,0,0],[0,np.cos(value),-np.sin(value)],[0,np.sin(value),np.cos(value)]])
				# py = np.array([[1,0,0],[0,np.cos(value),np.sin(value)],[0,-np.sin(value),np.cos(value)]])
				# Rotation about real world y (GPU x).
				gpu = np.array([[np.cos(value),0,-np.sin(value)],[0,1,0],[np.sin(value),0,np.cos(value)]])
			elif axis == 1:
				# Rotation about real world y.
				py = np.array([[np.cos(value),0,np.sin(value)],[0,1,0],[-np.sin(value),0,np.cos(value)]])
				gpu = np.array([[1,0,0],[0,np.cos(value),-np.sin(value)],[0,np.sin(value),np.cos(value)]])
			elif axis == 2:
				# Rotation about real world z.
				py = np.array([[np.cos(value),-np.sin(value),0],[np.sin(value),np.cos(value),0],[0,0,1]])
				gpu = np.array([[np.cos(value),np.sin(value),0],[-np.sin(value),np.cos(value),0],[0,0,1]])
			else:
				py = np.identity(3)
				gpu = np.identity(3)
			# Multiply into final matrix.
			pymat = pymat@py
			gpumat = gpumat@gpu

		return np.array(pymat).astype(np.float32), np.array(gpumat).astype(np.float32)

	def rotateWithOffset(self,point,rotation,offset):
		'''
		Rotate a point about an offset.
		'''
		# Rotation matrix.
		R = np.identity(4)
		R[:3,:3] = rotation
		# Translation matrix.
		T = np.identity(4)
		T[:3,3] = -offset
		# Inverse translation.
		Ti = np.identity(4)
		# Ti[:3,3] = offset
		Ti[:3,3] = (R@np.hstack([offset,1]))[:3]
		# print(Ti)
		# Make the point.
		p = np.hstack([point,1])
		# Translate, rotate, and reposition the point.
		# print('point:',p)
		P = T@p
		# print('translated:',P)
		P = R@P
		# print('rotated:',P)
		P = Ti@P
		# print('R:')
		# print(R)
		# print('T:')
		# print(T)
		# print('Ti:')
		# print(Ti)
		# print('Everything')
		# print(T@R@Ti)

		# P = T@R@Ti@p
		# print('rehomed:',P)

		return P[:3]

