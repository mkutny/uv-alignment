# Task: we have a face photo and a rorresponding face 3d-mesh.
# We want camera to view this face photo morphed (blended) into 3d-mesh of that face.
#
# For this task we setup a camera, a 3d-mesh and a photo (on a plane) in between.
# 
# The code below aligns photo with 3d-mesh from camera perspective.
# We use eyes and mouth landmarks for alignment.
#
# v.01 we can align two eyes between 

import bpy, bmesh
from mathutils import Vector, Matrix
from mathutils.geometry import intersect_ray_tri
from bpy_extras.view3d_utils import region_2d_to_vector_3d
from bpy_extras.view3d_utils import location_3d_to_region_2d
from math import cos, sin
import numpy as np

# Briefly, our approach is the following:
# 1. Find projection of mesh's coordinates on photo-plane
#  1.1 Get landmarks' world coordinates of 3d mesh
#  1.2 Find out corresponding screen coordinates
#  1.3 Project rays from located screen points back to landmarks
#  1.4 Find out intersection with our plane
#  1.5 Convert plane landmarks to UV-space
# 2. Get photo landmarks coordinates
#  2.1 Import photo landmarks
#  2.2 Convert to UV-space
# 3. Find affine transformation between two corresponding points on plane and photo
# 4. Transform UV map so the photo would match the plane


#######################################################################################
### GETTING WORLD COORDINATES OF 3D MESH LANDMARKS

# getting world coordinates of vertex 29478 (center of left eye of the mesh)
boy_obj = bpy.data.objects["BoyMorphed"]
eyeL_3D_world = boy_obj.matrix_world * boy_obj.data.vertices[29478].co

# getting world coordinates of vertex 29783 (center of right eye)
eyeR_3D_world = boy_obj.matrix_world * boy_obj.data.vertices[29783].co 


#######################################################################################
### FIND OUT CORRESPONDING SCREEN COORDINATES

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

# region - part of screen area in Blender; 
# rv3d - region that has 3D view (we can see our 3D scene through this region)
region, rv3d = view3d_find()

# looking for position of eyes and mouth in screeen coordinates (in pixels). 0,0 - left bottom corner of 3dview region
eyeL_2D_px = location_3d_to_region_2d(region, rv3d, eyeL_3D_world)
eyeR_2D_px = location_3d_to_region_2d(region, rv3d, eyeR_3D_world)


#######################################################################################
### PROJECT RAYS FROM SCREEN POINTS BACK TO LANDMARKS

# direction from camera origin to left eye
eyeL_ray_dir = region_2d_to_vector_3d (region, rv3d, eyeL_2D_px)
# direction from camera origin to right eye
eyeR_ray_dir = region_2d_to_vector_3d (region, rv3d, eyeR_2D_px)

#looking for camera location because ray looks from camera location
camera_origin = scene.objects.get('pasted__sc02_sh0010__camera_v002').location


#######################################################################################
### FIND OUT INTERSECTION WITH OUR PLANE

boy_photo_plane = scene.objects.get('BoyFotoPlane')

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

# get intersection world coordinates
eyeL_plane_glob = get_intesection (boy_photo_plane, camera_origin, eyeL_ray_dir)
eyeR_plane_glob = get_intesection (boy_photo_plane, camera_origin, eyeR_ray_dir)

# convert coordinates of intersection from world to FotoPlane's local
# local coordinates of BoyFotoPlane start in center and have axis X = looking right, Y = 0, Z = looking down
eyeL_plane_local = boy_photo_plane.matrix_world.inverted() * eyeL_plane_glob
eyeR_plane_local = boy_photo_plane.matrix_world.inverted() * eyeR_plane_glob


#######################################################################################
### CONVERT PLANE LANDMARK COORDINATES TO UV-space

# ToDo - could it be taken from plane properties?
# Yes, but I know only one way - for certain vertex. 
# For example boy_photo_plane.data.vertices[0].co.z
# In other words, I'm looking for vertex local coordinates in some corner of the plane
photo_plane_size = 4.71391 * 2 # width/height of the BoyFotoPlane in units (because width=height)

# convert to uv-coordinates: (0,0) is bottom left, (1,1) is top right
# normalizing coordinates of left eye intersection from local to range (0,0)-(1,1) and inverting Z axis
eyeL_plane_norm_x = (eyeL_plane_local[0] + photo_plane_size/2) / photo_plane_size
eyeL_plane_norm_z = 1 - (eyeL_plane_local[2] + photo_plane_size/2) / photo_plane_size

# normalizing coordinates of right eye intersection from local to range (0,0)-(1,1) and inverting Z axis
eyeR_plane_norm_x = (eyeR_plane_local[0] + photo_plane_size/2) / photo_plane_size
eyeR_plane_norm_z = 1 - (eyeR_plane_local[2] + photo_plane_size/2) / photo_plane_size

print ("Right Eye Plane normalized coordinates = ", eyeR_plane_norm_x, eyeR_plane_norm_z)
print ("Left Eye Plane normalized coordinates = ", eyeL_plane_norm_x, eyeL_plane_norm_z)


#######################################################################################
### GET PHOTO LANDMARK COORDINATES
# getting coordinates of eyes on photo from FaceGen

# x=0, z=0 are in the left top of the photo.
# z looking down.
# I named vertical axis as z because
# when I'm using local coordinates of BoyFotoPlane I have axis x and z (y = 0 for all vertices).
eyeL_photo_x = 471 # x position of the left eye on the photo in pixels
eyeL_photo_z = 1024-731 # z position of the left eye on the photo in pixels

eyeR_photo_x = 184 # x position of the right eye on the photo in pixels
eyeR_photo_z = 1024-688 # z position of the right eye on the photo in pixels

photo_x_size = 764 # width of the photo in pixels
photo_z_size = 1024 # height of the photo in pixels


#######################################################################################
### CONVERT PHOTO COORDS TO UV-SPACE

# normalizing coordinates of left eye on the photo from pixels to (0,0)-(1,1) and inverting Z axis
eyeL_photo_norm_x = eyeL_photo_x / photo_x_size
eyeL_photo_norm_z = 1 - eyeL_photo_z / photo_z_size

# normalizing coordinates of right eye on the photo from pixels to (0,0)-(1,1) and inverting Z axis
eyeR_photo_norm_x = eyeR_photo_x / photo_x_size
eyeR_photo_norm_z = 1 - eyeR_photo_z / photo_z_size

print ("Right Eye Foto normalized coordinates = ", eyeR_photo_norm_x, eyeR_photo_norm_z)
print ("Left Eye Foto normalized coordinates = ", eyeL_photo_norm_x, eyeL_photo_norm_z)


#######################################################################################
### FIND AFFINE TRANSFORMATION (ROTATION, SCALE, TRANSLATION)

# Now we have (all in UV-space):
# - landmarks' coordinates on plane
# - UV map of the plane (source map)
# - landmarks' coordinates on photo
# We are looking for a target UV map which would align photo with landmarks of 3D eyes on plane
#
# If we know affine transformation between plane's and photo's landmarks we could
# compute transformation matrix 'T'.
#
# TODO 2 lines below is not clear for me
# Given transformation matrix 'T' and plane's UV map 'plane_uv' one would find photo's
# UV map 'photo_uv' simply by dot product:  photo_uv = T * plane_uv
#
# Translation matrix 'T' has a form of:
# | s*cos(r) -s*sin(r)  tx |
# | s*sin(r)  s*cos(r)  ty |
# | 0         0         1  |
# where 's' is uniform scale, 'r' is rotation angel, '(tx, ty)' is a translation
#
# Given for 4 unknowns 's', 'r', 'tx', 'ty' we could solve for 'T' using 2 pairs of known
# correspondencies (e.g. two eyes).
#
# Let a = s*cos(r), b = s*sin(r)
# (x1, y1), (x2, y2) - eyes' coordinates on the plane
# (xp1, yp1), (xp2, yp2) - corresponding eyes' coordinates on the photo
#
# Then
# | x1 -y1 1 0 |   | a  |   | xp1 |
# | y1  x1 0 1 | * | b  | = | yp1 |
# | x2 -y2 1 0 |   | tx |   | xp2 |
# | y2  x2 0 1 |   | ty |   | yp2 |
#
# or 'source_matrix' * 'transform_vector' = 'prime_vector'
#
# Then transform_vector = inv(source_matrix) * prime_vector

# source x and y's
src_mat = Matrix.Translation ((1,2,3))

src_mat [0] = [eyeR_plane_norm_x, -eyeR_plane_norm_z, 1, 0]
src_mat [1] = [eyeR_plane_norm_z,  eyeR_plane_norm_x, 0, 1]
src_mat [2] = [eyeL_plane_norm_x, -eyeL_plane_norm_z, 1, 0]
src_mat [3] = [eyeL_plane_norm_z,  eyeL_plane_norm_x, 0, 1]

# target x and y's
prime_vec = Vector ((eyeR_photo_norm_x, eyeR_photo_norm_z, eyeL_photo_norm_x, eyeL_photo_norm_z))

# transform vector (a, b, tx, ty)
t_vec = np.dot(np.linalg.inv(src_mat), prime_vec)

t_mat = Matrix.Translation ((1,2,3)).to_3x3 ()

t_mat [0] = [t_vec[0], -t_vec[1], t_vec[2]]
t_mat [1] = [t_vec[1], t_vec[0], t_vec[3]]
t_mat [2] = [0, 0, 1]



#######################################################################################
### APPLY AFFINE TRANSFORMATION

# transforming uv
uv_map = boy_photo_plane.data.uv_layers.active
for v in boy_photo_plane.data.loops :
    uv_vec = uv_map.data[v.index].uv # uv vector

    uv_tr = t_mat * Vector((uv_vec[0], uv_vec[1], 1)) # transformed vector

    uv_vec[0] = uv_tr[0]
    uv_vec[1] = uv_tr[1]
