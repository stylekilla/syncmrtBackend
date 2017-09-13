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
		# Input array shape.
		self.in_shape = [0,0,0]
		# Placeholder for output array.
		self.arrOut = None

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

	def copyArrayToDevice(self,data,pixelSize=None,extent=None,isocenter=None):
		'''
		Here we give the data to be copied to the GPU and give some deacriptors about the data.
		We must enforce float32 datatypes as the kernels are assumed to be written in these also.
		'''
		# Create memory flags.
		mf = cl.mem_flags
		# Enforce float32 for input array.
		input = np.array(data).astype(np.float32)
		# Create empty input 3d image on device.
		self.in_image = cl.Image(self.ctx,
			mf.READ_ONLY,
			cl.ImageFormat(cl.channel_order.INTENSITY, cl.channel_type.FLOAT),
			input.shape)
		# Copy host content over to 3d image on device.
		cl.enqueue_copy(self.queue, self.in_image, input, origin=(0,0,0), region=input.shape)
		print('Copy Host to Dev')
		print(self.in_image.array_size)

		# Set some params for later.
		self.in_shape = input.shape
		self.pixelSize = pixelSize
		self.isocenter = isocenter
		# Extent[l,r,b,t,f,b]
		self.extent = extent
		# Trigger for setting bottom left corner as 0,0,0.
		self.zeroExtent = False

		# Create memory buffer for the array on the GPU in the current context.
		# dst_image = cl.Image(ctx, mf.WRITE_ONLY , f, shape=(100,100,4))
		# self.in_buff = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=input)

	def test(self):
		# We are going to copy the array back and see if the data handling is working.
		self.out_shape = self.in_shape
		# self.out_image = cl.Image(self.ctx,
		# 	mf.WRITE_ONLY,
		# 	cl.ImageFormat(cl.channel_order.INTENSITY, cl.channel_type.FLOAT),
		# 	self.out_shape)
		self.out_data = np.zeros(self.out_shape)

		# cl.enqueue_copy(self.queue, self.out_data, self.in_image, origin=(0, 0, 0), region=self.in_shape)
		# cl.enqueue_copy(self.queue, self.out_data, self.in_image, origin=(0,0,0), region=(3,3,3))
		self.out_data = self.in_image.get()
		print(self.out_data)

	def rotate(self,active,passive):
		'''
		rotate.cl accepts exactly 5 parameters (each of dtype float32):
			input					: Input Array
			activeRotation			: Active Rotation Matrix
			passiveRotation			: Passive Rotation Matrix
			output 					: Output Array
			outShape				: Output Array Size
		Returns new array and extent.
		'''
		mf = cl.mem_flags
		# Load the rotation program.
		self.loadProgram("rotate")
		# Enforce datatypes.
		active = np.array(active).astype(np.float32)
		passive = np.array(passive).astype(np.float32)
		# Input Buffers
		activeRotation_buff = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=active)
		passiveRotation_buff = cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=passive)

		# Create the output array.
		# Get output shape by rotating bounding box of vertice points.
		vert000 = active@ np.array([0,0,0]) @passive
		vert100 = active@ np.array((self.in_shape[0],0,0)) @passive
		vert010 = active@ np.array((0,self.in_shape[1],0)) @passive
		vert110 = active@ np.array((self.in_shape[0],self.in_shape[1],0)) @passive
		vert001 = active@ np.array((0,0,self.in_shape[2])) @passive
		vert101 = active@ np.array((self.in_shape[0],0,self.in_shape[2])) @passive
		vert011 = active@ np.array((0,self.in_shape[1],self.in_shape[2])) @passive
		vert111 = active@ self.in_shape @passive
		vertices = np.vstack([vert000,vert100,vert010,vert110,vert001,vert101,vert011,vert111])
		# Find minimum and maximum vertice points.
		minimum = np.amin(vertices,axis=0)
		maximum = np.amax(vertices,axis=0)
		# Find the difference between the two as a whole number.
		shape = maximum-minimum
		self.outputShape = np.rint(shape).astype(np.int32)
		# Set output (enforce float32)
		self.output = np.zeros(self.outputShape,dtype=np.float32,order='C')
		# self.out_buff = cl.Buffer(self.ctx, mf.WRITE_ONLY | mf.COPY_HOST_PTR, hostbuf=self.output)
		self.out_buff = cl.Image(self.ctx,
			mf.WRITE_ONLY,
			cl.ImageFormat(cl.channel_order.INTENSITY, cl.channel_type.FLOAT),
			self.outputShape)

		# Run program
		kwargs = (self.in_buff,
			activeRotation_buff,
			passiveRotation_buff,
			self.out_buff,
			self.outputShape
			)
		self.program.rotate3d(self.queue,self.in_shape,None,*(kwargs))

		# Queue the copy of the array on the gpu to the array in python.
		# cl.enqueue_copy(self.queue, self.out_buff, self.output)
		cl.enqueue_copy(self.queue, self.out_buff, self.output, is_blocking=True, origin=(0, 0, 0), region=self.outputShape)

		return self.output

	def loadProgram(self,kernel):
		''' Takes in a kernel, adds it as a program.'''
		# Get working dir for python site modules.
		fp = site.getsitepackages()[0]
		# Read in the kernel.
		sourceKernel = open(fp+"/syncmrt/tools/opencl/kernels/"+kernel+".cl", "r").read()
		# Build the program in the current context.
		self.program = cl.Program(self.ctx,sourceKernel).build()