__kernel void rotate3d(
	__global const float *gpuIn,
	__global const float *gpuActiveRotation,
	__global const float *gpuPassiveRotation,
	__global float *gpuOut,
	__global const float *gpuOutShape)
{
	// Get global xyz ID's.
	int x = get_global_id(0);
	int y = get_global_id(1);
	int z = get_global_id(2);
	// printf("Global ID (%i %i %i) \n",x,y,z);

	// Get input sizes.
	int szx = get_global_size(0);
	int szy = get_global_size(1);
	int szz = get_global_size(2);
	// printf("Input Size (%i %i %i) \n",szx,szy,szz);

	// Get the ID number of the thread.
	int idx = z + (szz * y) + (szz * szy * x);
	// printf("Idx: %i\n",idx);

	// Get input origin (center of array).
	float inputOrigin[3] = {
		(szx-1)/2,
		(szy-1)/2,
		(szz-1)/2
	};

	// Move thread with respect to input origin.
	float i = x - inputOrigin[0];
	float j = y - inputOrigin[1];
	float k = z - inputOrigin[2];

	// printf("OutputShape: (%f %f %f)\n",gpuOutShape[0],gpuOutShape[1],gpuOutShape[2]);
	// printf("Input origin (%f %f %f) \n",inputOrigin[0],inputOrigin[1],inputOrigin[2]);
	// printf("Origin centered point (%f %f %f) \n",i,j,k);
	// printf("GPU Rotation (%f) \n",gpuActiveRotation[5]);

	// Rotate points (active).
	float point[3] = {
		i*gpuActiveRotation[0] + j*gpuActiveRotation[1] + k*gpuActiveRotation[2],
		i*gpuActiveRotation[3] + j*gpuActiveRotation[4] + k*gpuActiveRotation[5],
		i*gpuActiveRotation[6] + j*gpuActiveRotation[7] + k*gpuActiveRotation[8]
	};

	// Rotate points again (passive).
	float point2[3] = {
		point[0]*gpuPassiveRotation[0] + point[1]*gpuPassiveRotation[1] + point[2]*gpuPassiveRotation[2],
		point[0]*gpuPassiveRotation[3] + point[1]*gpuPassiveRotation[4] + point[2]*gpuPassiveRotation[5],
		point[0]*gpuPassiveRotation[6] + point[1]*gpuPassiveRotation[7] + point[2]*gpuPassiveRotation[8]
	};

	// printf("Rotated Point: %f,%f,%f \n",point2[0],point2[1],point2[2]);

	// New origin based of output shape size.
	float outOrigin[3] = {
		(gpuOutShape[0]-1)/2,
		(gpuOutShape[1]-1)/2,
		(gpuOutShape[2]-1)/2
	};
	// printf("Output Origin: %f,%f,%f \n",outOrigin[0],outOrigin[1],outOrigin[2]);

	// Relocate point in output shape.
	int newPoint[3] = {
		(int)(point2[0] + outOrigin[0]),
		(int)(point2[1] + outOrigin[1]),
		(int)(point2[2] + outOrigin[2])
	};
	// printf("New Point: %i,%i,%i \n",newPoint[0],newPoint[1],newPoint[2]);

	// idx is the new point id.
	int idxNew = newPoint[2] + 
		(gpuOutShape[2] * newPoint[1]) +
		(gpuOutShape[2] * gpuOutShape[1] * newPoint[0]);
	// printf("idxNew: %i\n",idxNew);

	//printf("sizeof(gpuOut), sizeof(gpuIn):, %i, %i\n", sizeof(&gpuOut), sizeof(&gpuIn));
	if(idxNew > (szx*szy*szz) -1) //54788095
	{
		idxNew = (szx *szy *szz) -1;
	};
	gpuOut[idxNew] = gpuIn[idx];

}