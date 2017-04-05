// #include <math.h>
#include <stdio.h>

#include <cmath>

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

	if ((x < texX) && (y < texY) && (z < texZ)) {
		// Center array (new origin). Relocated to 000.
		float texOrigin[3] = { 
			(texX-1)/2,
			(texY-1)/2,
			(texZ-1)/2 
		};

		// Adjust for origin.
		float i = x - texOrigin[0];
		float j = y - texOrigin[1];
		float k = z - texOrigin[2];

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

		// New origin based of output shape size.
		float outOrigin[3] = {
			((float)outX-1)/2,
			((float)outY-1)/2,
			((float)outZ-1)/2
		};

		// Relocate point in output shape.
		int newPoint[3] = {
			(int)roundf(point[0] + outOrigin[0]),
			(int)roundf(point[1] + outOrigin[1]),
			(int)roundf(point[2] + outOrigin[2])
		};

		int idx = newPoint[2] + 
		(outZ * newPoint[1]) +
		(outZ * outY * newPoint[0]);

		// printf("Cuda thread (%i %i %i); Center origin (%f %f %f); New location (%f %f %f); Un-centered origin (%i %i %i) \n",x,y,z,i,j,k,point[0],point[1],point[2],newPoint[0],newPoint[1],newPoint[2]);

		if (idx < (outX*outY*outZ)) {
			out[idx] = tex3D(tex, z, y, x);
			// printf("Coordinate %i %i %i Destination %i %i %i, Idx %i \n",x,y,z, newPoint[0],newPoint[1],newPoint[2],idx);
			// printf("val %f \n",tex3D(tex,8,0,0));
			// float value = tex3D(tex, z, y, x);
			// printf("Coordinate %i %i %i Value %f Destination %i %i %i, Idx %i \n",x,y,z,value, newPoint[0],newPoint[1],newPoint[2],idx);
			// printf("%f\n",tex3D(tex,0,0,2));
		}
		else {
			// printf("Vertex rotation failed with coordinate %i %i %i Destination %i %i %i, Idx %i \n",x,y,z, newPoint[0],newPoint[1],newPoint[2],idx);
			// printf("%f %f %f, %f %f %f, %f %f %f \n ",R[0][0],R[0][1],R[0][2],R[1][0],R[1][1],R[1][2],R[2][0],R[2][1],R[2][2]);
			// printf("Hello from coord %i %i %i Destination: %i %i %i \n",x,y,z, newPoint[0],newPoint[1],newPoint[2]);
			// printf("Accessing %i %i %i with constraints: %f %f %f \n",x,y,z, texX,texY,texZ);
		}

	}

}