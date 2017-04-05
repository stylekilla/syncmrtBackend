import os
import sys
from natsort import natsorted

def importImage(path,modality,ftype):
	path = path
	dataset = []

	# Create list of accepted file extensions.
	if ftype == 'tiff':
		ext = ['.tif','.tiff']
	elif ftype == 'png':
		ext = ['.png']
	elif ftype == 'jpg':
		ext = ['.jpg','.jpeg']
	elif ftype == 'npy':
		ext = ['.npy']

	# Walk directory and generate list of files in it.
	for root, subdir, fp in os.walk(path):
		for fn in fp:
			if (fn.endswith(tuple(ext))) & (fn[:len(modality)] == modality):
			# if (fn.endswith(tuple(ext))):
				dataset.append(os.path.join(root,fn))

	# Sort for natural sorting.
	dataset = natsorted(dataset)

	return dataset