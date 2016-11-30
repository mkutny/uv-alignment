# Start match_foto_with_3D function to transform UV of Girl's FotoPlane based on coordinates
# of eyes and mouth on Photo: eR, eL, mR, mL,
# where X = 0, Y = 0 in the tob left corner of the photo. Y points downwards.

# Blender need this to find uv_alignment_functions.py and use match_foto_with_3D function inside
import os, sys
lib_path = os.path.abspath(os.path.join('d:\\desktop\\Matching-Photo-n-3D-4UE\\code\\uv-alignment\\'))
sys.path.append(lib_path)

from math import radians, pi
from mathutils import Vector
from uv_alignment_functions import match_foto_with_3D

# for xml parsing
import xml.etree.ElementTree as ET

# these transformations moves baked girl to position of skinned girl
location = (0.16856, 0.13704, 0.02343)
rotation = (pi/2, 0, radians (-69.89))
scale = (0.0085, 0.0085, 0.0085)

AR_plane = 1.44 # aspect ratio of Girl's FotoPlane

gender = "Girl"

data = "d:\Girl.xml"
tree = ET.parse(data)
root = tree.getroot()
eR = Vector((int(root[0][9][0].text), int(root[0][9][1].text))) # right eye coordinates
eL = Vector((int(root[0][8][0].text), int(root[0][8][1].text))) # left eye coordinates
mR = Vector((int(root[0][7][0].text), int(root[0][7][1].text))) # right corner of mouth coordinates
mL = Vector((int(root[0][6][0].text), int(root[0][6][1].text))) # left corner of mouth coordinates

shapekey_eyes_path = "d:\Girl-eyes-shapekey.obj"
shapekey_head_path = "d:\Girl-head-shapekey.obj"

# NOTE! Path to foto texture of GirlFotoPlane - "d:\Girl-photo-limbo.jpg".
# If you need, you can change it inside blender file 01A_Limbo_sc01_sh0030_OnlyGirl.blend

match_foto_with_3D (eR, eL, mR, mL, gender, shapekey_eyes_path, shapekey_head_path, location, rotation, scale, AR_plane)

