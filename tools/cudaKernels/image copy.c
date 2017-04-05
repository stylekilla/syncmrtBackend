#include <math.h>
#include <stdio.h>

texture<float, 3, cudaReadModeElementType> tex;

__global__ void rotate(
	float *out,
	float rotX,
	float rotY,
	float rotZ,
	float texX,
	float texY,
	float texZ,
	int outX,
	int outY,
	int outZ)
{
	// Global thread indexes in each axis.
	int x = blockIdx.x*blockDim.x + threadIdx.x;
	int y = blockIdx.y*blockDim.y + threadIdx.y;
	int z = blockIdx.z*blockDim.z + threadIdx.z;

	//Center array (new origin). Relocated to 000.
	float orgx = (texX-1)/2;
	float orgy = (texY-1)/2;
	float orgz = (texZ-1)/2;

	float i = x - orgx;
	float j = y - orgy;
	float k = z - orgz;

	// Calculate rotation matrix (Rx*Ry*Rz).
	float R[3][3] = {
		{ 	cos(rotY)*cos(rotZ),
			cos(rotY)*sin(rotZ),
			-sin(rotY) } ,
		{   sin(rotX)*sin(rotY)*cos(rotZ)-cos(rotX)*sin(rotZ),
			sin(rotX)*sin(rotY)*sin(rotZ)+cos(rotX)*cos(rotZ),
			sin(rotX)*cos(rotY) } ,
		{	cos(rotX)*sin(rotY)*cos(rotZ)+sin(rotX)*sin(rotZ),
			cos(rotX)*sin(rotY)*sin(rotZ)-sin(rotX)*cos(rotZ),
			cos(rotX)*cos(rotY) }
	};

	// Rotate points.
	float point[3] = {
		i*R[0][0] + j*R[0][1] + k*R[0][2],
		i*R[1][0] + j*R[1][1] + k*R[1][2],
		i*R[2][0] + j*R[2][1] + k*R[2][2]
	};

	// Rotate origin.
	float origin[3] = {
		fabs(orgx*R[0][0] + orgy*R[0][1] + orgz*R[0][2]),
		fabs(orgx*R[1][0] + orgy*R[1][1] + orgz*R[1][2]),
		fabs(orgx*R[2][0] + orgy*R[2][1] + orgz*R[2][2])
	};

	// Refocus point to old origin (0,0,0).
	int newPoint[3] = {
		(int)roundf(point[0] + origin[0]),
		(int)roundf(point[1] + origin[1]),
		(int)roundf(point[2] + origin[2])
	};

	int idx = newPoint[0] + 
		(outX * newPoint[1]) +
		(outX * outY * newPoint[2]);



	if 	((newPoint[0] >= 0) && (newPoint[1] >= 0) && (newPoint[2] >= 0)) {
		if ((newPoint[0] < outX) && (newPoint[1] < outY) && (newPoint[2] < outZ)) {

			// If we are in the bounds of the texture then copy the information.
			out[idx] = tex3D(tex, x, y, z);

		}
	}
}