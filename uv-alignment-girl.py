import os, sys
from math import radians, pi,
from mathutils import Vector
lib_path = os.path.abspath(os.path.join('d:\\desktop\\Matching-Photo-n-3D-4UE\\code\\uv-alignment\\'))
sys.path.append(lib_path)
from uv_alignment_functions import match_foto_with_3D
import xml.etree.ElementTree as ET
import urllib.request as RQ


location = (0.16856, 0.13704, 0.02343)
rotation = (pi/2, 0, radians (-69.89))
scale = (0.0085, 0.0085, 0.0085)
AR_plane = 1.44 # aspect ratio of Girl's FotoPlane

gender = "Girl"

avatar = 76 # ID of avatar

data = RQ.urlopen("http://face3d.unteleported.com/avatars/{}/photo.bpt.xml".format(avatar))
tree = ET.parse(data)
root = tree.getroot()
eR = Vector((int(root[0][2][0].text), int(root[0][2][1].text))) # right eye coordinates
eL = Vector((int(root[0][3][0].text), int(root[0][3][1].text))) # left eye coordinates


RQ.URLopener().retrieve ("http://face3d.unteleported.com/avatars/{}/Eyes.obj".format(avatar), "d:\Girl-eyes-shapekey.obj")
shapekey_eyes_path = "d:\Girl-eyes-shapekey.obj"
RQ.URLopener().retrieve ("http://face3d.unteleported.com/avatars/{}/Head.obj".format(avatar), "d:\Girl-head-shapekey.obj")
shapekey_head_path = "d:\Girl-head-shapekey.obj"

RQ.URLopener().retrieve ("http://face3d.unteleported.com/avatars/{}/photo.jpg".format(avatar), "d:\Girl-photo-limbo.jpg")
match_foto_with_3D (eR, eL, gender, shapekey_eyes_path, shapekey_head_path, location, rotation, scale, AR_plane)

RQ.URLopener().retrieve ("http://face3d.unteleported.com/avatars/{}/Head1.jpg".format(avatar), "d:\Girl-head-texture.jpg")


# start match_foto_with_3D function to transform UV of Girl's FotoPlane based on coordinates
# of eyes on Photo:
# lx, ly, rx, ry - left eye X, left eye Y, right eye X, right eye Y,
# where X = 0, Y = 0 in the tob left corner of the photo. Y points downwards.
# match_foto_with_3D (968, 677, 654, 673, fbx_path, shapekey_eyes_path, shapekey_head_path, location, rotation, scale, AR_plane) # for square photo