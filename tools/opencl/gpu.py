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

	# def rotate(self,data,activeRotation=(0,0,0),passiveRotation=(0,0,0),pixelSize=(1,1,1),extent=(-1,1,-1,1,-1,1),isocenter=None):
	def rotate(self,data,activeRotation=[],passiveRotation=[],pixelSize=(1,1,1),extent=(-1,1,-1,1,-1,1),isocenter=None):
		'''
		Here we give the data to be copied to the GPU and give some deacriptors about the data.
		We must enforce float32 datatypes as the kernels are assumed to be written in these also.
		'''
		# Enforce float32 for arrIn array.
		# arrIn = np.array(data,order='C').astype(np.float32)
		arrIn = np.array(data,order='C').astype(np.int32)

		# Deal with rotations.
		activeRotation = self.rotationMatrix(activeRotation)
		passiveRotation = self.rotationMatrix(passiveRotation)

		# x,y,z = np.deg2rad(activeRotation)
		# # y,x,z = np.deg2rad(activeRotation)
		# rx = np.array([[1,0,0],[0,np.cos(x),-np.sin(x)],[0,np.sin(x),np.cos(x)]])
		# ry = np.array([[np.cos(y),0,-np.sin(y)],[0,1,0],[np.sin(y),0,np.cos(y)]])
		# rz = np.array([[np.cos(z),-np.sin(z),0],[np.sin(z),np.cos(z),0],[0,0,1]])
		# activeRotation = np.array(rz@ry@rx).astype(np.float32)
		# x,y,z = np.deg2rad(passiveRotation)
		# # y,x,z = np.deg2rad(passiveRotation)
		# rx = np.array([[1,0,0],[0,np.cos(x),-np.sin(x)],[0,np.sin(x),np.cos(x)]])
		# ry = np.array([[np.cos(y),0,-np.sin(y)],[0,1,0],[np.sin(y),0,np.cos(y)]])
		# rz = np.array([[np.cos(z),-np.sin(z),0],[np.sin(z),np.cos(z),0],[0,0,1]])
		# passiveRotation = np.array(rz@ry@rx).astype(np.float32)

		# Input Shape
		inputShape = np.array([
			[0,0,0],
			[1,0,0],
			[0,1,0],
			[1,1,0],
			[0,0,1],
			[1,0,1],
			[0,1,1],
			[1,1,1]]) * arrIn.shape

		# Output shape.
		outputShape = np.empty(inputShape.shape,dtype=int)
		for i in range(8):
			outputShape[i,:] = activeRotation@inputShape[i,:]@passiveRotation
		mins = np.absolute(np.amin(outputShape,axis=0))
		maxs = np.absolute(np.amax(outputShape,axis=0))
		outputShape = mins+maxs

		# Create output array.
		arrOut = np.zeros(outputShape).astype(np.int32)-1000
		arrOutShape = np.array(arrOut.shape).astype(np.int32)

		# DATA TRANSFER
		# Create memory flags.
		mf = cl.mem_flags
		# GPU buffers.
		gpuIn = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=arrIn)
		gpuActiveRotation = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=activeRotation)
		gpuPassiveRotation = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=passiveRotation)
		gpuOut = cl.Buffer(self.ctx, mf.WRITE_ONLY | mf.COPY_HOST_PTR, hostbuf=arrOut)
		gpuOutShape = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=arrOutShape)

		# RUN THE PROGRAM
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
		# Run
		program.rotate3d(self.queue,arrIn.shape,None,*(kwargs))
		# program.rotate3d(self.queue,arrIn.shape,None,*(kwargs)).wait()

		# Get results
		cl.enqueue_copy(self.queue, arrOut, gpuOut)

		# Remove dirty information.
		arrOut = np.nan_to_num(arrOut)

		# Change other vars.
		if pixelSize is not None: self.pixelSize = activeRotation@pixelSize@passiveRotation
		if isocenter is not None: self.isocenter = activeRotation@isocenter@passiveRotation
		# Extent[l,r,b,t,f,b]
		if extent is not None: 
			inputExtent = np.array([
				[extent[2],extent[0],extent[4]],
				[extent[2],extent[1],extent[4]],
				[extent[3],extent[0],extent[4]],
				[extent[3],extent[1],extent[4]],
				[extent[2],extent[0],extent[5]],
				[extent[2],extent[1],extent[5]],
				[extent[3],extent[0],extent[5]],
				[extent[3],extent[1],extent[5]]])

			# Output extent.
			outputExtent = np.empty(inputExtent.shape)
			for i in range(8):
				outputExtent[i,:] = activeRotation@inputExtent[i,:]@passiveRotation
			mins = np.amin(outputExtent,axis=0)
			maxs = np.amax(outputExtent,axis=0)
			# Final output for extent.
			# self.extent = np.array([mins[0],maxs[0],mins[1],maxs[1],mins[2],maxs[2]])
			self.extent = np.array([mins[1],maxs[1],mins[0],maxs[0],mins[2],maxs[2]])
			# self.extent = np.array([-10,10,-10,10,-10,10])

		# Trigger for setting bottom left corner as 0,0,0.
		self.zeroExtent = False

		return arrOut

	def rotationMatrix(self,rotationList):
		# rotationList should be a list of strings that match: '0123.1' where the first character, 0/1/2 represents the axis, the rest represents the value to rotate by.
		# Begin with identity matrix.
		matrix = np.identity(3)
		# Iterate through desired rotations.
		for i in range(len(rotationList)):
			axis = int(rotationList[i][0])
			value = np.deg2rad(float(rotationList[i][1:]))
			if axis == 0:
				temp = np.array([[1,0,0],[0,np.cos(value),-np.sin(value)],[0,np.sin(value),np.cos(value)]])
			elif axis == 1:
				temp = np.array([[np.cos(value),0,-np.sin(value)],[0,1,0],[np.sin(value),0,np.cos(value)]])
			elif axis == 2:
				temp = np.array([[np.cos(value),-np.sin(value),0],[np.sin(value),np.cos(value),0],[0,0,1]])
			else:
				temp = np.identity(3)
			# Multiply into final matrix.
			matrix = matrix@temp
		return np.array(matrix).astype(np.float32)