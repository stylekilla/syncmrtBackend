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

	def rotate(self,data,activeRotation=[],passiveRotation=[],pixelSize=None,extent=None,isocenter=None):
		'''
		Here we give the data to be copied to the GPU and give some deacriptors about the data.
		We must enforce datatypes as we are dealing with c and memory access/copies.
		Rotations happen about real world (x,y,z) axes.
		'''
		tmpisocprint = isocenter
		# Read in array and force the datatype for the gpu.
		arrIn = np.array(data,order='C').astype(np.int32)

		# Get rotation matrices.
		activeRotation = self.rotationMatrix(activeRotation)
		passiveRotation = self.rotationMatrix(passiveRotation)

		# Create a basic box for calculations of a cube.
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
			outputShape[i,:] = activeRotation@inputShape[i,:]@passiveRotation
		mins = np.absolute(np.amin(outputShape,axis=0))
		maxs = np.absolute(np.amax(outputShape,axis=0))
		outputShape = mins+maxs

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
		gpuActiveRotation = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=activeRotation)
		gpuPassiveRotation = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=passiveRotation)
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
			gpuActiveRotation,
			gpuPassiveRotation,
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
		self.axes = np.rint(np.absolute(passiveRotation@np.array([0,1,2])@activeRotation)).astype(int)

		# Rotate the pixelSize if specified.
		if pixelSize is not None: 
			# Pixel size comes in as (x,y,z), we need to make it (y,x,z) to make it compatible with python.
			print('pixel size in:',pixelSize)
			pixelSize = np.array([pixelSize[1], pixelSize[0], pixelSize[2]])
			# Apply the rotations.
			print('pixel rearranged:',pixelSize)
			pixelSize = passiveRotation@pixelSize@activeRotation
			# Convert back to real world (from python).
			print('pixel rotated:',pixelSize)
			self.pixelSize = np.array([pixelSize[1], pixelSize[0], pixelSize[2]])
			print('pixel out:',self.pixelSize)

		# Rotate the isocenter if specified.
		if isocenter is not None: 
			# The isocenter comes in as (x,y,z), we need to make it (y,x,z) to make it compatible with python.
			print('isocenter original:',isocenter)
			isocenter = np.array([isocenter[1], isocenter[0], isocenter[2]])
			# Get the isocenter according to the new axes.
			print('isocenter swapped:',isocenter)
			isocenter = np.array([isocenter[self.axes[0]], isocenter[self.axes[1]], isocenter[self.axes[2]]])
			print('isocenter rotated:',isocenter)
			# Convert back to real world (from python).
			self.isocenter = np.array([isocenter[1], isocenter[0], isocenter[2]])
			print('isocenter swapped:',self.isocenter)

		if extent is not None: 
			# Make the 8 corners of the bounding box as (y,x,z) coordinates for python.
			inputExtent = np.array([
				[extent[2],extent[0],extent[4]],
				[extent[2],extent[1],extent[4]],
				[extent[3],extent[0],extent[4]],
				[extent[3],extent[1],extent[4]],
				[extent[2],extent[0],extent[5]],
				[extent[2],extent[1],extent[5]],
				[extent[3],extent[0],extent[5]],
				[extent[3],extent[1],extent[5]]])

			# Make another 8 corner array for the testing.
			test = np.empty(inputExtent.shape)

			# For each basic box corner, rotate it.
			for i in range(8):
				test[i,:] = passiveRotation@basicBox[i,:]@activeRotation

			# Find the minimum point in each direction of the basic box.
			minimumPoints = np.argmin(test,axis=0)

			# Add 1 to output shape for extent (one extra pixel involved).
			outputShape += 1

			# Use the position of the minimum points
			x1 = inputExtent[minimumPoints[1],self.axes[1]]
			x2 = x1 + outputShape[1]*pixelSize[1]
			y1 = inputExtent[minimumPoints[0],self.axes[0]]
			y2 = y1 + outputShape[0]*pixelSize[0]
			z1 = inputExtent[minimumPoints[2],self.axes[2]]
			z2 = z1 + outputShape[2]*pixelSize[2]

			# Compile values into extent.
			self.extent = np.array([x1,x2,y1,y2,z1,z2])

			# print('====================== GPU ======================')
			# print('inputExtent',extent)
			# print('inputExtent Box')
			# print(inputExtent)
			# print('test')
			# print(test)
			# print('minimum vals',minimumPoints)
			# print('output axes',self.axes)
			# print('output extent',self.extent)
			# print('output shape',outputShape)
			# print('pixel size',pixelSize)
			# print('isocenter before',tmpisocprint)
			# print('isocenter after',self.isocenter)

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
		matrix = np.identity(3)
		# Iterate through desired rotations.
		for i in range(len(rotationList)):
			axis = int(rotationList[i][0])
			value = np.deg2rad(float(rotationList[i][1:]))
			if axis == 1:
				# Rotation about real world x.
				temp = np.array([[1,0,0],[0,np.cos(value),-np.sin(value)],[0,np.sin(value),np.cos(value)]])
			elif axis == 0:
				# Rotation about real world y.
				temp = np.array([[np.cos(value),0,-np.sin(value)],[0,1,0],[np.sin(value),0,np.cos(value)]])
			elif axis == 2:
				# Rotation about real world z.
				temp = np.array([[np.cos(value),-np.sin(value),0],[np.sin(value),np.cos(value),0],[0,0,1]])
			else:
				temp = np.identity(3)
			# Multiply into final matrix.
			matrix = matrix@temp

		print('Rotation List:',rotationList)
		print('Rotation Matrix:')
		print(matrix)

		return np.array(matrix).astype(np.float32)