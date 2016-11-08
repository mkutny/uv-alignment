import os, sys
from math import radians, pi
lib_path = os.path.abspath(os.path.join('d:\\desktop\\Matching-Photo-n-3D-4UE\\code\\uv-alignment\\'))
sys.path.append(lib_path)
from uv_alignment_functions import match_foto_with_3D


location = (0.16856, 0.13704, 0.02343)
rotation = (pi/2, 0, radians (-69.89))
scale = (0.0085, 0.0085, 0.0085)
fbx_path = "d:\desktop\Matching-Photo-n-3D-4UE\sc01_sh0030_GirlFotoPlane_transfUV.fbx"
shapekey_eyes_path = "d:\desktop\Reconstruction-kids-for-clients\BeautifulGirl\BeautifulGirl-Eyes.obj"
shapekey_head_path = "d:\desktop\Reconstruction-kids-for-clients\BeautifulGirl\BeautifulGirl-head.obj"
AR_plane = 1.44 # aspect ratio of Girl's FotoPlane

# start match_foto_with_3D function to transform UV of Girl's FotoPlane based on coordinates
# of eyes on Photo:
# lx, ly, rx, ry - left eye X, left eye Y, right eye X, right eye Y,
# where X = 0, Y = 0 in the tob left corner of the photo. Y points downwards.
match_foto_with_3D (968, 677, 654, 673, fbx_path, shapekey_eyes_path, shapekey_head_path, location, rotation, scale, AR_plane) # for square photo