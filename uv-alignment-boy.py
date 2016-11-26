import os, sys
from math import pi
from mathutils import Vector
lib_path = os.path.abspath(os.path.join('d:\\desktop\\Matching-Photo-n-3D-4UE\\code\\uv-alignment\\'))
sys.path.append(lib_path)
from uv_alignment_functions import match_foto_with_3D
import xml.etree.ElementTree as ET
import urllib.request as RQ


location = (0, 0, 0)
rotation = (pi/2, 0, 0)
scale = (0.01, 0.01, 0.01)
AR_plane = 1.44  # aspect ratio of Boy's FotoPlane

gender = "Boy"

avatar = 103 # ID of avatar

data = RQ.urlopen("http://face3d.unteleported.com/avatars/{}/photo.bpt.xml".format(avatar))
tree = ET.parse(data)
root = tree.getroot()
eR = Vector((int(root[0][9][0].text), int(root[0][9][1].text))) # right eye coordinates
eL = Vector((int(root[0][8][0].text), int(root[0][8][1].text))) # left eye coordinates


RQ.URLopener().retrieve ("http://face3d.unteleported.com/avatars/{}/Eyes.obj".format(avatar), "d:\Boy-eyes-shapekey.obj")
shapekey_eyes_path = "d:\Boy-eyes-shapekey.obj"
RQ.URLopener().retrieve ("http://face3d.unteleported.com/avatars/{}/Head.obj".format(avatar), "d:\Boy-head-shapekey.obj")
shapekey_head_path = "d:\Boy-head-shapekey.obj"

RQ.URLopener().retrieve ("http://face3d.unteleported.com/avatars/{}/photo.jpg".format(avatar), "d:\Boy-photo-limbo.jpg")
match_foto_with_3D (eR, eL, gender, shapekey_eyes_path, shapekey_head_path, location, rotation, scale, AR_plane)

RQ.URLopener().retrieve ("http://face3d.unteleported.com/avatars/{}/Head1.jpg".format(avatar), "d:\Boy-head-texture.jpg")
RQ.URLopener().retrieve ("http://face3d.unteleported.com/avatars/{}/boy.fbx".format(avatar), "d:\Boy.fbx")

# start match_foto_with_3D function to transform UV of Boy's FotoPlane based on coordinates
# of eyes on Photo:
# lx, ly, rx, ry - left eye X, left eye Y, right eye X, right eye Y,
# where X = 0, Y = 0 in the tob left corner of the photo. Y points downwards.

# match_foto_with_3D (2202, 860, 1889, 745, fbx_path, shapekey_eyes_path, shapekey_head_path, location, rotation, scale, AR_plane) # for landscape aspect ratio = 2.03:1
# match_foto_with_3D (241, 374, 235, 665, fbx_path, shapekey_eyes_path, shapekey_head_path, location, rotation, scale, AR_plane) # for AR=1.44, 90 deg rotatio
# match_foto_with_3D (559, 294, 345, 490, fbx_path, shapekey_eyes_path, shapekey_head_path, location, rotation, scale, AR_plane) # for AR=1.44, 45 deg rotatio
# match_foto_with_3D (733, 626, 400, 626, fbx_path, shapekey_eyes_path, shapekey_head_path, location, rotation, scale, AR_plane) # for real aspect ratio
# match_foto_with_3D (958, 691, 625, 693, fbx_path, shapekey_eyes_path, shapekey_head_path, location, rotation, scale, AR_plane) # for square photo