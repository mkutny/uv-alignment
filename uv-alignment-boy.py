import os, sys
from math import pi
lib_path = os.path.abspath(os.path.join('d:\\desktop\\Matching-Photo-n-3D-4UE\\code\\uv-alignment\\'))
sys.path.append(lib_path)
from uv_alignment_functions import match_foto_with_3D


location = (0, 0, 0)
rotation = (pi/2, 0, 0)
scale = (0.01, 0.01, 0.01)
fbx_path = "d:\desktop\Matching-Photo-n-3D-4UE\sc01_sh0030_BoyFotoPlane_transfUV.fbx"
shapekey_eyes_path = "d:\desktop\Reconstruction-kids-for-clients\BeautifulBoy\BeautifulBoy-Eyes.obj"
shapekey_head_path = "d:\desktop\Reconstruction-kids-for-clients\BeautifulBoy\BeautifulBoy-Head.obj"
AR_plane = 1.44  # aspect ratio of Boy's FotoPlane

# start match_foto_with_3D function to transform UV of Boy's FotoPlane based on coordinates
# of eyes on Photo:
# lx, ly, rx, ry - left eye X, left eye Y, right eye X, right eye Y,
# where X = 0, Y = 0 in the tob left corner of the photo. Y points downwards.

match_foto_with_3D (2202, 860, 1889, 745, fbx_path, shapekey_eyes_path, shapekey_head_path, location, rotation, scale, AR_plane) # for landscape aspect ratio = 2.03:1
# match_foto_with_3D (241, 374, 235, 665, fbx_path, shapekey_eyes_path, shapekey_head_path, location, rotation, scale, AR_plane) # for AR=1.44, 90 deg rotatio
# match_foto_with_3D (559, 294, 345, 490, fbx_path, shapekey_eyes_path, shapekey_head_path, location, rotation, scale, AR_plane) # for AR=1.44, 45 deg rotatio
# match_foto_with_3D (733, 626, 400, 626, fbx_path, shapekey_eyes_path, shapekey_head_path, location, rotation, scale, AR_plane) # for real aspect ratio
# match_foto_with_3D (958, 691, 625, 693, fbx_path, shapekey_eyes_path, shapekey_head_path, location, rotation, scale, AR_plane) # for square photo