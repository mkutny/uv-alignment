# v.01 we can align two eyes

import bpy, bmesh
from mathutils import Vector, Matrix
from mathutils.geometry import intersect_ray_tri
from bpy_extras.view3d_utils import region_2d_to_vector_3d
from bpy_extras.view3d_utils import location_3d_to_region_2d
from math import cos, sin

# todo
# 1.1. move timeslider to 336 frame for boy
# 1.2. converting coordinates of vertices in center of 3D eyes from local to world space

# 2.1. find coordinates of 3D eyes in pixelspace of screen
# 2.2. find intersections of ray from 3D eyes with BoyFotoPlane (world space)
# 2.3. converting intersection from world space to local space of BoyFotoPlane where axis X = x, Y = -z
# 2.4. normalizing intersection and fixing Z axis (we need to do it because Z must look up)

# 3.1. getting coordinates of eyes on photo from FaceGen
# 3.2. normalize coordinates of eyes on photo

# 4.1. creating matrix of transformation
# 4.2. transforming uv

#######################################################################################
################################## 1.2 ################################################
#######################################################################################

#getting world coordinates of vertex 29478 in the center of left eye
eyeL3D_wco = bpy.data.objects["BoyMorphed"].matrix_world*bpy.data.objects["BoyMorphed"].data.vertices[29478].co 
#getting world coordinates of vertex 29783 in the center of right eye
eyeR3D_wco = bpy.data.objects["BoyMorphed"].matrix_world*bpy.data.objects["BoyMorphed"].data.vertices[29783].co 




#######################################################################################
################################## 2.1 ################################################
#######################################################################################

scene = bpy.context.scene # getting current scene

# looking for 3d view. It MUST be one with Camera as main camera. 
# Camera frame must be visible completely in 3d view
def view3d_find():
    # returns first 3d view, normally we get from context
    for area in bpy.context.window.screen.areas:
        if area.type == 'VIEW_3D':
            v3d = area.spaces[0]
            rv3d = v3d.region_3d
            for region in area.regions:
                if region.type == 'WINDOW':
                    return region, rv3d
    return None, None

region, rv3d = view3d_find()

# looking for position of eyes and mouth in screeen coordinates (in pixels). 0,0 - left bottom corner of 3dview region
eyeL3D_px = location_3d_to_region_2d(region, rv3d, eyeL3D_wco)
eyeR3D_px = location_3d_to_region_2d(region, rv3d, eyeR3D_wco)

#######################################################################################
################################## 2.2 ################################################
#######################################################################################

# direction from camera origin to left eye
eyeL_ray_dir = region_2d_to_vector_3d (region, rv3d, eyeL3D_px)
# direction from camera origin to right eye
eyeR_ray_dir = region_2d_to_vector_3d (region, rv3d, eyeR3D_px)

#looking for camera location because ray looks from camera location
origin = scene.objects.get('pasted__sc02_sh0010__camera_v002').location

BoyFotoPlane = scene.objects.get('BoyFotoPlane')

# looking for the first intersection of line 
# (line between 2 points: ray_dir and origin)
# and FotoPlane
def get_intesection (ob, origin, ray_dir):
    if None not in (ob, origin, ray_dir) and ob.type == 'MESH':
        bm = bmesh.new()
        bm.from_object(ob, scene)
        bm.transform(ob.matrix_world)
        bmesh.ops.triangulate(bm, faces=bm.faces)
       
        for face in bm.faces:
            intersection = intersect_ray_tri(face.verts[0].co, face.verts[1].co, face.verts[2].co, ray_dir, origin)
            if intersection is not None:
                print("Intersection found:", intersection)
                
                # drawing cross in place of intersection
                inter = bpy.data.objects.new("Intersection", None)
                inter.location = intersection
                inter.empty_draw_size = 2
                scene.objects.link(inter)

                break # find the first intersection only
        scene.update()
    return intersection

interEyeL = get_intesection (BoyFotoPlane, origin, eyeL_ray_dir)
interEyeR = get_intesection (BoyFotoPlane, origin, eyeR_ray_dir)

#######################################################################################
################################## 2.3 ################################################
#######################################################################################

# convert coordinates of intersection from world to FotoPlane's local
# local coordinates of BoyFotoPlane start in center and have axis X = looking right, Y = 0, Z = looking down
interEyeL_local = BoyFotoPlane.matrix_world.inverted()*interEyeL
interEyeR_local = BoyFotoPlane.matrix_world.inverted()*interEyeR

#######################################################################################
################################## 2.4 ################################################
#######################################################################################

photoPlaneSize = 4.71391 # half width/height of the BoyFotoPlane in units (because width=height)

# normalizing coordinates of left eye intersection from local to range 0,0-1,1 and inverting Z axis
interEyeL_co_nx = ((interEyeL_local[0] + photoPlaneSize)/(photoPlaneSize))/2
interEyeL_co_nz = 1 - ((interEyeL_local[2] + photoPlaneSize)/(photoPlaneSize))/2

# normalizing coordinates of right eye intersection from local to range 0,0-1,1 and inverting Z axis
interEyeR_co_nx = ((interEyeR_local[0] + photoPlaneSize)/(photoPlaneSize))/2
interEyeR_co_nz = 1- ((interEyeR_local[2] + photoPlaneSize)/(photoPlaneSize))/2

print ("Right Eye Plane =", interEyeR_co_nx, interEyeR_co_nz)
print ("Left Eye Plane =", interEyeL_co_nx, interEyeL_co_nz)




#######################################################################################
################################## 3.1 ################################################
#######################################################################################

# getting coordinates of eyes on photo from FaceGen

# x=0, z=0 are in the center of the photo.
# z looking down.
# I named vertical axis as z because
# when I'm using local coordinates of BoyFotoPlane I have axis x and z (y = 0 for all vertices).
eyeL_photo_x = 89 # x position of the left eye on the photo in pixels
eyeL_photo_z = -219 # z position of the left eye on the photo in pixels

eyeR_photo_x = -198 # x position of the right eye on the photo in pixels
eyeR_photo_z = -176 # z position of the right eye on the photo in pixels

photo_x = 382 # half width of the photo in pixels
photo_z = 512 # half height of the photo in pixels

ar = 1.44151 # aspect ratio of BoyFotoPlane

#######################################################################################
################################## 3.2 ################################################
#######################################################################################

# normalizing coordinates of left eye on the photo from pixels to 0,0-1,1 and inverting Z axis
eyeL_foto_co_nx = ((eyeL_photo_x + photo_x)/(photo_x))/2
eyeL_foto_co_nz = 1 - ((eyeL_photo_z + photo_z)/(photo_z))/2

# normalizing coordinates of right eye on the photo from pixels to 0,0-1,1 and inverting Z axis
eyeR_foto_co_nx = ((eyeR_photo_x + photo_x)/(photo_x))/2
eyeR_foto_co_nz = 1 - ((eyeR_photo_z + photo_z)/(photo_z))/2

print ("Right Eye Foto =", eyeR_foto_co_nx, eyeR_foto_co_nz)
print ("Left Eye Foto =", eyeL_foto_co_nx, eyeL_foto_co_nz)




#######################################################################################
################################## 4.1 ################################################
#######################################################################################

# creating matrix 3x3 in this strange way (because I don't know how to do it in oter way)
matrixT = Matrix.Translation ((1,2,3)).to_3x3 ()

# filling matrix with values calculated with help of this https://github.com/axelpale/nudged-py
matrixT[0][0] = 1.320802769303709
matrixT[0][1] = -0.15099206295327702
matrixT[0][2] = -0.17697950213490118

matrixT[1][0] = 0.15099206295327702
matrixT[1][1] = 1.320802769303709
matrixT[1][2] = -0.0895266793498636

matrixT[2][0] = 0
matrixT[2][1] = 0
matrixT[2][2] = 1
#print (matrixT)

#######################################################################################
################################## 4.2 ################################################
#######################################################################################

# transforming uv
UVmap = BoyFotoPlane.data.uv_layers.active
for v in BoyFotoPlane.data.loops :
    uv_vec = UVmap.data[v.index].uv # uv vector

    uv_tr = matrixT * Vector((uv_vec[0], uv_vec[1], 1)) # transformed vector

    uv_vec[0] = uv_tr[0]
    uv_vec[1] = uv_tr[1]
