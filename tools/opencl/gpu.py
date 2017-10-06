import pyopencl as cl
import numpy as np
import site

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
	def __init__(self,deviceType='GPU'):
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

		# Find the current platform.
		platforms = cl.get_platforms()
		# Retrieve a device list.
		if deviceType == 'GPU':
			deviceList = platforms[0].get_devices(cl.device_type.GPU)
		else:
			# Choose a cpu?
			# In which case we would return to an equiv numpy routine.
			pass

		# Force looking for my GT970M for now, ideally this information would be kept in a config file.
		for testDevice in deviceList:
			if 'GT' in testDevice.name:
				device = testDevice

		# Create a device context.
		self.ctx = cl.Context(devices=[device])
		# Create a device queue.
		self.queue = cl.CommandQueue(self.ctx)

	def rotate(self,data,activeRotation=(0,0,0),passiveRotation=(0,0,0),pixelSize=(1,1,1),extent=(-1,1,-1,1,-1,1),isocenter=None):
		'''
		Here we give the data to be copied to the GPU and give some deacriptors about the data.
		We must enforce float32 datatypes as the kernels are assumed to be written in these also.
		'''
		# Enforce float32 for arrIn array.
		arrIn = np.array(data).astype(np.float32)
		# Deal with rotations.
		x,y,z = np.deg2rad(activeRotation)
		rx = np.array([[1,0,0],[0,np.cos(x),-np.sin(x)],[0,np.sin(x),np.cos(x)]])
		ry = np.array([[np.cos(y),0,-np.sin(y)],[0,1,0],[np.sin(y),0,np.cos(y)]])
		rz = np.array([[np.cos(z),-np.sin(z),0],[np.sin(z),np.cos(z),0],[0,0,1]])
		activeRotation = np.array(rz@ry@rx).astype(np.float32)
		x,y,z = np.deg2rad(passiveRotation)
		rx = np.array([[1,0,0],[0,np.cos(x),-np.sin(x)],[0,np.sin(x),np.cos(x)]])
		ry = np.array([[np.cos(y),0,-np.sin(y)],[0,1,0],[np.sin(y),0,np.cos(y)]])
		rz = np.array([[np.cos(z),-np.sin(z),0],[np.sin(z),np.cos(z),0],[0,0,1]])
		passiveRotation = np.array(rz@ry@rx).astype(np.float32)

		# Output size
		boundingBox = np.array([
			[0,0,0],
			[1,0,0],
			[0,1,0],
			[1,1,0],
			[0,0,1],
			[1,0,1],
			[0,1,1],
			[1,1,1]]) * arrIn.shape
		for i in range(8):
			boundingBox[i,:] = activeRotation@boundingBox[i,:]@passiveRotation
		boundingBox = np.amax(np.absolute(boundingBox),axis=0)

		# Create output array.
		arrOut = np.empty(boundingBox).astype(np.float32)
		arrOutShape = np.array(arrOut.shape).astype(np.float32)

		# DATA TRANSFER
		# Create memory flags.
		mf = cl.mem_flags
		# GPU buffers.
		gpuIn = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=arrIn)
		gpuActiveRotation = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=activeRotation)
		gpuPassiveRotation = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=passiveRotation)
		gpuOut = cl.Buffer(self.ctx, mf.WRITE_ONLY, arrOut.nbytes)
		gpuOutShape = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=arrOutShape)

		# RUN THE PROGRAM
		# Get kernel source.
		fp = site.getsitepackages()[0]
		sourceKernel = open(fp+"/syncmrt/tools/opencl/kernels/rotate.cl", "r").read()		
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
		program.rotate3d(self.queue,arrIn.shape,None,*(kwargs)).wait()

		# Get results
		cl.enqueue_copy(self.queue, arrOut, gpuOut)

		# Change other vars.
		if pixelSize is not None: self.pixelSize = activeRotation@pixelSize@passiveRotation
		if isocenter is not None: self.isocenter = activeRotation@isocenter@passiveRotation
		# Extent[l,r,b,t,f,b]
		if extent is not None: self.extent = extent
		# Trigger for setting bottom left corner as 0,0,0.
		self.zeroExtent = False

		return arrOut