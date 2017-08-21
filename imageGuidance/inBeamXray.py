'''
Scan object through beam and match detector frame rate to movement speed.
Need list of reccomended exposure times for kV selection/imaging target.
'''

from epics import PV

def acquireContinuous(verticalMotorPV,detectorPV,exposureTime=0.1,offset=0,height=100,filepath=''):
	# Connect motor PV's.
	motorMove = PV(verticalMotorPV+'.MOV')
	motorPos = PV(verticalMotorPV+'.RBV')
	motorSpeed = PV(verticalMotorPV+'.SPEED')

	# Connect detector PV's.
	detAcquire = PV(detectorPV+'.ACQUIRE')
	detOperationMode = PV(detectorPV+'.MODE')
	# detExposure = PV(detectorPV+'.RBV')
	# det = PV(detectorPV+'.SPEED')

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


def acquireScan(verticalMotorPV,detectorPV,exposureTime=0.1,offset=0,height=100,filepath=''):
	# Connect motor PV's.
	motorMove = PV(verticalMotorPV+'.MOV')
	motorPos = PV(verticalMotorPV+'.RBV')
	motorSpeed = PV(verticalMotorPV+'.SPEED')

	# Connect detector PV's.
	detAcquire = PV(detectorPV+'.ACQUIRE')
	detOperationMode = PV(detectorPV+'.MODE')
	# detExposure = PV(detectorPV+'.RBV')
	# det = PV(detectorPV+'.SPEED')

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