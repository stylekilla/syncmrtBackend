import math
import numpy as np
from syncmrt.tools.math import quaternion as quat

'''
ASSUMPTIONS:
	1. That the orientation of the two objects are the same vertically (i.e. one cannot be upside down and the other upright.)
	2. CT is left points in mm, XR is right points in mm.
	3. User origin is in relation to Dicom origin.
	4. All points are relative to the user origin.
	5. Both CT and Synchrotron orthogonal images are the same CW or CCW direction of the image.
'''

# Create a class to find the transform between two WCS's.
class affineTransform:
	def __init__(self,ctCS,synchCS,patientIsoc=None,synchIsoc=None,synchRotIsoc=None):
		self.advance = True

		if type(ctCS) == type(int()):
			'''If single integer, then pass back all zeroes.'''
			self.theta = 0
			self.phi = 0
			self.gamma = 0
			self.translation = np.array([0,0,0])
			self.scale = 0

			self.advance = False

		if self.advance == True:
			pass
		else:
			return

		'''Points should come in as xyz cols and n-points rows: np.array((n,xyz))'''
		self.n = np.shape(ctCS)[0]

		# LEFT and RIGHT points should be in mm.
		self.ct = ctCS
		self.synch = synchCS

		# Find the centroids of the LEFT and RIGHT WCS.
		self.ct_ctd = centroid(self.ct)
		self.synch_ctd = centroid(self.synch)

		# Find the LEFT and RIGHT points in terms of their centroids (notation: LEFT Prime, RIGHT Prime)
		self.ct_p = np.zeros([self.n,3])
		self.synch_p = np.zeros([self.n,3])

		for i in range(self.n):
			self.ct_p[i,:] = np.subtract(self.ct[i,:],self.ct_ctd)
			self.synch_p[i,:] = np.subtract(self.synch[i,:],self.synch_ctd)

		# Find the quaternion matrix, N.
		self.N = quaternion(self.ct_p,self.synch_p)

		# Solve eigenvals and vec that maximises rotation.
		val, self.vec = eigen(self.N)

		# Extract transformation quarternion from evec.
		self.q = np.zeros((4,))
		self.q[0] = self.vec[0][0]
		self.q[1] = self.vec[1][0]
		self.q[2] = self.vec[2][0]
		self.q[3] = self.vec[3][0]

		# Compute rotation matrix, R.
		self.R = rotationMatrix(self.q)
		self.R = np.reshape(self.R,(3,3))

		# Extract individual angles in degrees.
		self.rotation = angles(self.R,self.ct,self.synch)

		# The xray goal is always 0,0,0. The isoc of the coordinate system at IMBL.
		synchBeamIsoc = np.array([0,0,0])

		# If no patient isocenter is defined, align to the centroid.
		if patientIsoc is None:
			patientIsoc = self.ct_ctd

		# Centroid to ptv isoc (according to the treatment plan).
		ct_ctd2isoc = patientIsoc - self.ct_ctd

		# Move synchrotron centroid to beam isocenter.
		if synchRotIsoc is not None:
			# Find where the centroid is after rotation.
			self.synch_rotctd = np.dot(self.synch_ctd,self.R)
			translation1 = synchBeamIsoc - self.synch_rotctd
		else:
			translation1 = synchBeamIsoc - self.synch_ctd

		# Move patient isocenter to beam isocenter.
		translation2 = synchBeamIsoc + ct_ctd2isoc

		# Final translation is a combination of all other translations.
		self.translation = translation1 + translation2

		# Extract scale.
		if synchRotIsoc is not None:
			self.synch_p = np.zeros([self.n,3])
			for i in range(self.n):
				self.synch_p[i,:] = np.subtract(self.synch[i,:],self.synch_ctd)
		self.scale = scale(self.ct_p,self.synch_p,self.R)

		print('Results from solver.py')
		print('CT Centroid',self.ct_ctd)
		print('Synch Centroid',self.synch_ctd)
		print('CT Centroid to patisoc',ct_ctd2isoc)
		print('Translation 1: synchctd to beamisoc',translation1)
		print('Translation 2: patisoc to beamisoc',translation2)

# Obtain scale factor between coordinate systems. Requires left and right points in reference to centroids.
def scale(lp,rp,R):
	n = np.shape(lp)[0]

	D = np.zeros((n,1))
	S_l = np.zeros((n,1))

	for i in range(n):
		D[i,0] = np.dot(np.array([rp[i,:]]),np.dot(R,np.array([lp[i,:]]).T))[0][0]
		S_l[i,0] = np.linalg.norm(lp[i,:])**2

	return np.sum(D)/np.sum(S_l)

# Find the centroid of a set of points (pts).
def centroid(pts):
	print('centroid calc')
	print(pts)
	n = np.shape(pts)[0]
	ctd = (1/n)*np.sum(pts,axis=0)
	return ctd

# Pass left and right coordinate system points in and pass out the matrix N.
def quaternion(l,r):
	# Calculate sum of products matrix, M.
	M = np.dot(l.transpose(),r)

	# Calculate xx, xy, xz, yy ... zz. 
	sxx = M[0,0]
	sxy = M[0,1]
	sxz = M[0,2]
	syx = M[1,0]
	syy = M[1,1]
	syz = M[1,2]
	szx = M[2,0]
	szy = M[2,1]
	szz = M[2,2]

	# Calculate N
	N = np.array([[sxx+syy+szz, syz-szy, szx-sxz, sxy-syx],
	[syz-szy, sxx-syy-szz, sxy+syx, szx+sxz],
	[szx-sxz, sxy+syx, -sxx+syy-szz, syz+szy],
	[sxy-syx, szx+sxz, syz+szy, -sxx-syy+szz]])

	# Return the matrix N
	return N

#  Find the eigenvector and eigenvalue for a given matrix.
def eigen(arr):
	#  Find the eigen vector and value of the array, arr.
	e, v = np.linalg.eig(arr)

	#  Find the maximum eigen value and it's corresponding eigen vector.
	val = np.amax(e)
	ind = np.argmax(e)
	i = np.unravel_index(ind,np.shape(e))

	vec = v[:,i]

	# Return the maximum eigenvalue and corresponding eigenvector.
	return val, vec

# Find the rotation matrix for a given eigen-solution.
def rotationMatrix(q):
	#  Calculate rotation matrix, R, based off quarternion input. This should be the eigenvector solution to N.
	R = np.array([[(q[0]**2+q[1]**2-q[2]**2-q[3]**2), 2*(q[1]*q[2]-q[0]*q[3]), 2*(q[1]*q[3]+q[0]*q[2])],
	[2*(q[2]*q[1]+q[0]*q[3]), (q[0]**2-q[1]**2+q[2]**2-q[3]**2), 2*(q[2]*q[3]-q[0]*q[1])],
	[2*(q[3]*q[1]-q[0]*q[2]), 2*(q[3]*q[2]+q[0]*q[1]), (q[0]**2-q[1]**2-q[2]**2+q[3]**2)]])

	# Return the rotation matrix, R. This is in the form of Rz*Ry*Rx, x -> y -> z. 
	# This matrix is orthogonal (no translations or reflections.)
	return R

# Extract individual rotations around the x, y and z axis seperately. 
def angles(R,l,r):
	# Two possible angles for y.
	y = []
	y.append(np.arcsin(R[2][0]))
	y.append(np.pi-np.arcsin(R[2][0]))

	# Angle for Z
	z = []
	for i in range(len(y)):
		z.append(np.arctan2(R[1][0]/np.cos(y[i]),R[0][0]/np.cos(y[i])))


	# Angle for X
	x = []
	for i in range(len(y)):
		x.append(np.arctan2(R[2][1]/np.cos(y[i]),R[2][2]/np.cos(y[i])))

	success = False
	while (success is False):
		for i in range(len(y)):
			xx = np.rad2deg(x[i])
			yy = np.rad2deg(y[i])
			zz = np.rad2deg(z[i])

		if ((-95 < xx < 95) & (-95 < yy < 95) & (-360 < zz < 360)):
			success = True
		else:
			try:
				del x[i]
				del y[i]
				del z[i]
			except:
				print('\033[91m Unable to solve for the alignment. Please select the points properly.')
				return 0, 0, 0

	# Angles must be applied in xyz order.
	return np.array([xx,yy,zz])
