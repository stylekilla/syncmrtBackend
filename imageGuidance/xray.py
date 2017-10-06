'''
Scan object through beam and match detector frame rate to movement speed.
Need list of reccomended exposure times for kV selection/imaging target.
'''

from epics import PV
import h5py as hdf
import numpy as np

# Create an xray image set.
class xrayDataset:
	def __init__(self,fn):
		self.file = hdf.File(fn,"w")
		self.file.attrs['NumberOfImages'] = 2

		self._error = ['NO_DETECTOR_INFORMATION']

	def setDetector(self,detector):
		# Take variables from detector.
		self.file.attrs['Detector'] = detector.name
		self.file.attrs['PixelSize'] = detector.pixelSize
		self.file.attrs['imageSize'] = detector.imageSize
		self.file.attrs['imageIsocenter'] = detector.imageIsocenter
		self.file.attrs['imagePixelSize'] = detector.imagePixelSize
		# If successfull then remove the error.
		self._error.remove('NO_DETECTOR_INFORMATION')

	def save(self):
		if np.sum(self._check) == 4:
			self.file.close()
		else:
			print('Self check failed with ',self._check)


# # Instead of HDF5 this could become DICOM.
# f = hdf.File("test_image.hdf5","w")
# f.attrs['NumberOfImages'] = 2
# f.attrs['Detector'] = 'Hamamatsu'
# f.attrs['PixelSize'] = 0.200
# f.attrs['PatientName'] = 'Bob'

# im1 = f.create_dataset('0',data=npyArr)
# im2 = f.create_dataset('1',data=npyArr)

# im1.attrs['extent'] = np.array([0,0,0,0])
# im1.attrs['isocenter'] = np.array([0,0,0])

# # Save
# f.close()

# # Reading
# f['0'][:]
# f['0'].attrs['extent']



# OLD STUFF ________

def acquire(mode):
	# step and shoot.
	# scan - not yet supported.
	pass

def acquireContinuous(verticalMotorPV,detPV,exposureTime=0.1,offset=0,height=100,filepath=''):
	# Connect motor PV's.
	motorMove = PV(verticalMotorPV+'.MOV')
	motorPos = PV(verticalMotorPV+'.RBV')
	motorSpeed = PV(verticalMotorPV+'.SPEED')

	# Connect detector PV's.
	detAcquire = PV(detPV+'.ACQUIRE')
	detOperationMode = PV(detPV+'.MODE')
	# detExposure = PV(detPV+'.RBV')
	# det = PV(detPV+'.SPEED')

	# Get the original starting position of the motor.
	origin = verticalMotorPos.get()

	# pixel size = speed * exposure time

	# Work out motor speed and refresh rate of detector.
	exposureTime = 0.01

	refreshRate = 1/(exposureTime)
	detExposure.set(refreshRate)

	speed = pixelSize/exposureTime
	motorSpeed.set(speed)

	# Set detector operation mode to continuous.
	detOperationMode.set('CONTINUOUS')

	# Move to some offset location. This should be from the current location to the bottom of the object (with some wiggle room).
	motorMove.set(origin-offset)

	# Start motor scan motion through to height of object.
	tmp = motorPos.get()
	motorMove.set(tmp+height)

	# Start data acquisition.
	detAcquire.set(1)

	# Stop data acquisition.
	detAcquire.set(0)

class detector:
	def __init__(self,name,pv):
		self._name = str(name)
		self._pv = str(pv)

	def setup(self):
		self._acquire = PV(self._pv+':CAM:Acquire')
		# Region of interest.
		self._roix = PV(':CAM:SizeX_RBV')
		self._roiy = PV(':CAM:SizeY_RBV')
		self.roi = [self._roix,self._roiy]

	def setVariable(self,**kwargs):
		# Kwargs should be in the form of a dict: {'key'=value}.
		for key, value in kwargs:
			# Assumes correct value type for keyword argument.
			epics.caput(self._pv+str(key),value)

	def acquire(self):
		# Tell the detector to acquire an image.
		self._acquire.put(1)

def stepAndShoot(detector,stage):
	'''
	detector		Detector class object, hardware.detector()
	stage			Stage class object, hardware.stage()
	'''
	# Intital detector setup.
	kwargs = {':CAM:ImageMode':0,			# ImageMode = Single
	':CAM:ArrayCounter':0,					# ImageCounter = 0
		':TIFF:AutoSave':1,					# AutoSave = True
		':TIFF:FileName':'scan',			# FileName = 'scan1'
		':TIFF:AutoIncrement':1,			# AutoIncrement = True
		':TIFF:FileNumber':0				# NextFileNumber = 0
		}
	# epics.caput(dtr_pv+':TIFF:FileTemplate','%s%s_%02d.tif')		# Filename Format
	detector.setVariable(**kwargs)

	# Record intial position to put everything back to after we finish.
	_intialPosition = stage.position()

	# Move to lower Z limit via translation.
	stage.move(object_bottom,axis=2,mode='absolute')
	# Get z position after move.
	object_pos = stage.position()[2]

	# Take an image.
	detector.acquire()

	# Delta H, the amount to move in the vertical direction for each step.
	d_h = detector.roi[1]*0.95

	while object_pos < object_top:
		# Move 90% of the region of interest down.
		stage.move(d_h,axis=2,mode='relative')
		# Acquire and image.
		detector.acquire()
		# Update z position.
		object_pos = stage.position()[2]
		# Repeat until we have reached our object_top point.

	# Once finished, move the object back to the start.
	stage.move(_initialPosition,mode='absolute')

	# Now reconstruct the image!