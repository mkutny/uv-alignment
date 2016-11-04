import os, sys
lib_path = os.path.abspath(os.path.join('d:\\desktop\\Matching-Photo-n-3D-4UE\\code\\uv-alignment\\'))
sys.path.append(lib_path)
from uv_alignment_functions import start

# start startBoy function to transform UV of Boy's FotoPlane based on coordinates
# of eyes on Photo:
# lx, ly, rx, ry - left eye X, left eye Y, right eye X, right eye Y,
# where X = 0, Y = 0 in the tob left corner of the photo. Y points downwards.
start(968, 677, 654, 673, 'Boy')