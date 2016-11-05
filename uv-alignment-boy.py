import os, sys
from math import pi
lib_path = os.path.abspath(os.path.join('d:\\desktop\\Matching-Photo-n-3D-4UE\\code\\uv-alignment\\'))
sys.path.append(lib_path)
from uv_alignment_functions import start


location = (0, 0, 0)
rotation = (pi/2, 0, 0)
scale = (0.01, 0.01, 0.01)
fbx_path = "d:\desktop\Matching-Photo-n-3D-4UE\sc01_sh0030_BoyFotoPlane_transfUV.fbx"
# start startBoy function to transform UV of Boy's FotoPlane based on coordinates
# of eyes on Photo:
# lx, ly, rx, ry - left eye X, left eye Y, right eye X, right eye Y,
# where X = 0, Y = 0 in the tob left corner of the photo. Y points downwards.
start(958, 691, 625, 693, fbx_path, location, rotation, scale)