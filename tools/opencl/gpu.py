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
		# self.ctx = cl.Context(devices=[cpuList[0]])
		self.ctx = cl.Context(devices=[gpuList[0]])
		# Create a device queue.
		self.queue = cl.CommandQueue(self.ctx)

	def rotate(self,data,rotations=[],pixelSize=None,extent=None,isocenter=None):
		'''
		Here we give the data to be copied to the GPU and give some deacriptors about the data.
		We must enforce datatypes as we are dealing with c and memory access/copies.
		Rotations happen about real world (x,y,z) axes.
		'''
		tmpisocprint = isocenter
		# Read in array and force the datatype for the gpu.
		arrIn = np.array(data,order='C').astype(np.int32)

		# Get rotation matrices for GPU.
		# test = np.array(rotations)
		# for i in range(len(rotations)):
		# 	temp = list(rotations[i])
		# 	if test[i][0] == '0': 
		# 		temp[0] = '1'
		# 	elif test[i][0] == '1': 
		# 		temp[0] = '0'
		# 	temp = ''.join(temp)
		# 	test[i] = temp
		# gpu_rotations = self.rotationMatrix(test)
		# print(rotations,test)
		# Rotation matrices for python.
		rotations,gpuRotations = self.rotationMatrix(rotations)

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

		print('In Shape',arrIn.shape)
		print('Out Shape',outputShape)

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

		# These are the axes for indexing (y,x,z)-python format.
		# Now rotate the axes so we know which one becomes which, direction is irrelevant so we can take the absolute value. This is for indexing purposes.
		# axes = np.rint(np.absolute(rotations@np.array([0,1,2])@rotations)).astype(int)
		pyAxes = np.rint(np.absolute(rotations@np.array([0,1,2]))).astype(int)
		# Get axes directions.
		axes = np.sign(pixelSize).astype(int)

		# Rotate the pixelSize if specified.
		if pixelSize is not None: 
			# Pixel size comes in as (x,y,z), we need to make it (y,x,z) to make it compatible with python.
			# print('pixel size in:',pixelSize)
			# pixelSize = np.array([pixelSize[1], pixelSize[0], pixelSize[2]])
			# print('pixel rearranged:',pixelSize)
			# Apply the rotations.
			print('pixel input:',pixelSize)
			self.pixelSize = rotations@pixelSize
			print('pixel rotated:',self.pixelSize)
			# Convert back to real world (from python).
			# self.pixelSize = np.array([pixelSize[1], pixelSize[0], pixelSize[2]])
			# print('pixel out:',self.pixelSize)

		# Rotate the isocenter if specified.
		if isocenter is not None: 
			# The isocenter comes in as (x,y,z), we need to make it (y,x,z) to make it compatible with python.
			# print('isocenter original:',isocenter)
			# isocenter = np.array([isocenter[1], isocenter[0], isocenter[2]])
			# print('isocenter swapped:',isocenter)
			# Get the isocenter according to the new axes.
			print('isocenter input:',isocenter)
			self.isocenter = (rotations@isocenter)*np.sign(self.pixelSize).astype(int)
			# self.isocenter = np.array([isocenter[pyAxes[0]], isocenter[pyAxes[1]], isocenter[pyAxes[2]]])
			print('isocenter rotated:',self.isocenter)
			print('Rotations')
			print(rotations)
			# Convert back to real world (from python).
			# self.isocenter = np.array([isocenter[1], isocenter[0], isocenter[2]])
			# print('isocenter swapped:',self.isocenter)

		if extent is not None: 
			# Make the 8 corners of the bounding box as (y,x,z) coordinates for python.
			# inputExtent = np.array([
			# 	[extent[0],extent[2],extent[4]],
			# 	[extent[1],extent[2],extent[4]],
			# 	[extent[0],extent[3],extent[4]],
			# 	[extent[1],extent[3],extent[4]],
			# 	[extent[0],extent[2],extent[5]],
			# 	[extent[1],extent[2],extent[5]],
			# 	[extent[0],extent[3],extent[5]],
			# 	[extent[1],extent[3],extent[5]]])

			basicBox = np.array([
				[0,0,0],
				[1,0,0],
				[0,1,0],
				[1,1,0],
				[0,0,1],
				[1,0,1],
				[0,1,1],
				[1,1,1]]).astype(np.float64)

			# Set box corners to reflect axis directions.
			basicBox *= np.sign(pixelSize)
			mins = np.min(basicBox,axis=0)
			maxs = np.max(basicBox,axis=0)

			print('Basic Box Axes Ordered')
			print(basicBox)

			inputExtent = np.zeros(basicBox.shape)

			# Construct extent box.
			for i in range(3):
				if pixelSize[i] < 0:
					# Negative Direction.
					inputExtent[:,i] += (basicBox==mins[i])[:,i]*extent[i*2+1]
					inputExtent[:,i] += (basicBox==maxs[i])[:,i]*extent[i*2]
				else:
					# Positive direction.
					inputExtent[:,i] += (basicBox==mins[i])[:,i]*extent[i*2]
					inputExtent[:,i] += (basicBox==maxs[i])[:,i]*extent[i*2+1]

			print('Input Extent')
			print(inputExtent)

			# Make another 8 corner array to rotate the basic box and see the outcome.
			test = np.empty(inputExtent.shape)

			# Reconfigure basic box to updated axes.
			# basicBox *= axes

			# temp = np.array(basicBox)
			# basicBox[:,0], basicBox[:,1], basicBox[:,2] = temp[:,axes[0]], temp[:,axes[1]], temp[:,axes[2]]
			# print('reordered basic box')
			# print(basicBox)

			outputExtent = np.array(inputExtent)

			# For each basic box corner, rotate it.
			for i in range(8):
				# test[i,:] = gpuRotations@basicBox[i,:]
				test[i,:] = rotations@basicBox[i,:]
				outputExtent[i,:] = rotations@inputExtent[i,:]

			print('Output Extent')
			print(outputExtent)

			# pyAxes2 = np.rint(np.absolute(rotations@pyAxes)).astype(int)

			# print('Baisc Rotated Box:')
			# print(test)
			# print('Rotated Input Extent:')
			# print(outputExtent)

			# Find the minimum point in each direction of the basic box.
			minimumPoints = np.argmin(test,axis=0)
			maximumPoints = np.argmax(test,axis=0)

			print('minimumPoints:',minimumPoints)
			print('maximumPoints:',maximumPoints)

			print('pyAxes:',pyAxes)
			# print('pyAxes2:',pyAxes2)

			# # New array size:
			# shape = np.array([arrIn.shape[1],arrIn.shape[0],arrIn.shape[2]])
			# size = shape*self.pixelSize

			# print('shape',shape)
			# print('size',size)

			# # New pixel shape
			# shape = np.array([outputShape[1],outputShape[0],outputShape[2]])
			# self.pixelSize = size/shape
			# print('New pixel size:',self.pixelSize)

			# Add 1 to output shape for extent (one extra pixel involved).
			outputShape += 1

			# Use the position of the minimum points
			x1 = outputExtent[minimumPoints[0],0]
			x2 = outputExtent[maximumPoints[0],0]
			# x2 = x1 + outputShape[1]*self.pixelSize[0]
			y1 = outputExtent[minimumPoints[1],1]
			y2 = outputExtent[maximumPoints[1],1]
			# y2 = y1 + outputShape[0]*self.pixelSize[1]
			z1 = outputExtent[minimumPoints[2],2]
			z2 = outputExtent[maximumPoints[2],2]
			# z2 = z1 + outputShape[2]*self.pixelSize[2]

			# Compile values into extent.
			self.extent = np.array([x1,x2,y1,y2,z1,z2])

			print('In Extent',extent)
			print('Out Extent',self.extent)

		# Trigger for setting bottom left corner as 0,0,0. WHAT EVEN IS THIS???
		self.zeroExtent = False

		return arrOut

	def rotationMatrix(self,rotationList):

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