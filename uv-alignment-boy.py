# Task: we have a face photo and a face 3d-mesh reconstructed from it.
#
# We have a task of bringing photo and 3d-mesh in correspondence so that
# their predefined landmarks are aligned from camera perspective.
#
# For this task we setup a camera, a 3d-mesh and a photo (on a plane)
# in between camera and mesh.
#
# v.01 We rely on left and rigth eyes to be our predefined landmarks

import bpy, bmesh
from mathutils import Vector, Matrix
from math import pi, radians
from mathutils.geometry import intersect_ray_tri
from bpy_extras.view3d_utils import region_2d_to_vector_3d
from bpy_extras.view3d_utils import location_3d_to_region_2d

# Briefly, our approach is the following:
# 1. Find projection of mesh's landmarks on photo-plane
#  1.1 Get landmarks' world coordinates of 3d mesh
#  1.2 Find out corresponding screen coordinates
#  1.3 Project rays from located screen points back to landmarks
#  1.4 Find out intersection with our plane
#  1.5 Convert plane landmarks to UV-space
# 2. Get photo's landmarks' coordinates
#  2.1 Import photo landmarks
#  2.2 Convert to UV-space
# 3. Find affine transformation between two corresponding points on plane and photo
# 4. Transform UV map so the photo would match the plane


#######################################################################################
### GETTING WORLD COORDINATES OF 3D MESH LANDMARKS

scene = bpy.context.scene # getting current scene

# select skinned eyes
eyes = bpy.data.objects["BoyEyes"]

# apply skin to mesh (bake skin)
def skinedMeshToMesh (skinnedMesh):
    # apply all modifiers (and skin also)
    tomesh = skinnedMesh.to_mesh (scene, 1, 'RENDER')
    # convert mesh to object
    obj = bpy.data.objects.new ("Baked" + skinnedMesh.name, tomesh)
    # link object to scene
    scene.objects.link(obj)
    # select eyes
    obj.select = True
    return obj

def applyBoyTransformation (obj):
    # rotate and scale eyes to match skinned
    obj.rotation_euler[0] = pi/2
    obj.scale = (0.01, 0.01, 0.01)
    # select eyes
    obj.select = True
    bpy.ops.object.transform_apply (location=True, rotation=True, scale=True)

eyes_obj = skinedMeshToMesh (eyes)
applyBoyTransformation (eyes_obj)
# getting world coordinates of vertex 192 - center of left eye
eyeL_3D_world = eyes_obj.matrix_world * eyes_obj.data.vertices[192].co
# getting world coordinates of vertex 385 - center of right eye
eyeR_3D_world = eyes_obj.matrix_world * eyes_obj.data.vertices[385].co 



#######################################################################################
### FIND OUT CORRESPONDING SCREEN COORDINATES

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

# looking for position of eyes and mouth in screeen coordinates
eyeL_2D_px = location_3d_to_region_2d(region, rv3d, eyeL_3D_world)
eyeR_2D_px = location_3d_to_region_2d(region, rv3d, eyeR_3D_world)
# print ("Girl's eyes in pixels =", eyeL_2D_px, eyeR_2D_px)


#######################################################################################
### PROJECT RAYS FROM SCREEN POINTS BACK TO LANDMARKS

# direction from camera origin to left eye
eyeL_ray_dir = region_2d_to_vector_3d (region, rv3d, eyeL_2D_px)
# direction from camera origin to right eye
eyeR_ray_dir = region_2d_to_vector_3d (region, rv3d, eyeR_2D_px)
# print ("direction =", eyeL_ray_dir, eyeR_ray_dir)

#looking for camera location because ray looks from camera location
camera_origin = scene.objects.get('cam_boy').location
#print ("cam location =", camera_origin)


#######################################################################################
### FIND OUT INTERSECTION WITH OUR PLANE

photo_plane = scene.objects.get('BoyFotoPlane')
#print ("photo_plane =", photo_plane)

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
        
    return intersection

# get intersection world coordinates
eyeL_plane_glob = get_intesection (photo_plane, camera_origin, eyeL_ray_dir)
eyeR_plane_glob = get_intesection (photo_plane, camera_origin, eyeR_ray_dir)
# convert coordinates of intersection from world to FotoPlane's local
# local coordinates of BoyFotoPlane start in center and have axis X = looking right, Y = 0, Z = looking down
eyeL_plane_local = photo_plane.matrix_world.inverted() * eyeL_plane_glob
eyeR_plane_local = photo_plane.matrix_world.inverted() * eyeR_plane_glob



#######################################################################################
### CONVERT PLANE LANDMARK COORDINATES TO UV-space

# ToDo - could it be taken from plane properties?
# Yes, but I know only one way - for certain vertex. 
# For example photo_plane.data.vertices[0].co.z
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
eyeL_photo_x = 471      # x position of the left eye on the photo in pixels
eyeL_photo_z = 1024-731 # z position of the left eye on the photo in pixels

eyeR_photo_x = 184      # x position of the right eye on the photo in pixels
eyeR_photo_z = 1024-688 # z position of the right eye on the photo in pixels

photo_x_size = 764      # width of the photo in pixels
photo_z_size = 1024     # height of the photo in pixels


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

# We want to find such an affine transformation 'T' that brings photo and plane points
# in correspondence: photo_points = T * plane_points
#
# More precisely 'T' is called Affine Transformation Matrix and is written in a form:
#
#                | s*cos(r)  -s*sin(r)  tx |
# photo_points = | s*sin(r)   s*cos(r)  ty | * plane_points     (Equation 1)
#                | 0          0         1  |
#
# where 'r' is CCW rotation, 's' is uniform scale and 'tx', 'ty' are translation parameters.
#
# Given 4 unknown parameters 's*cos(r)', 's*sin(r)', 'tx', 'ty' there are 4 equations
# needed to solve for 'T' and 4 corresponding knowns to populate these equations.
# Hopefully one pair of correspoinding landmakrs gives us as much as 2 known parameters
# (their 'x' and 'y' coords) therefore we need only 2 pairs of corresponding landmarks
# between plane and photo (i.e. left and right eyes) to compute 'T'.
#
# Let (plane_x1, plane_y1), (plane_x2, plane_y2) be eyes' coordinates on the plane and
# (photo_x1, photo_y1), (photo_x2, photo_y2) corresponding eyes' coordinates on the photo
# that we calculated on previous steps.
#
# Then equation 1 is solved for 's*cos(r)', 's*sin(r)', 'tx', 'ty' by the solution:
# | s*cos(r) |   | plane_x1  -plane_y1  1  0 |-1   | photo_x1 |
# | s*sin(r) | = | plane_y1   plane_x1  0  1 |   * | photo_y1 |
# | tx       |   | plane_x2  -plane_y2  1  0 |     | photo_x2 |
# | ty       |   | plane_y2   plane_x2  0  1 |     | photo_y2 |
#

# Populate matrix with plane's X's and Y's
plane_mat = Matrix(([eyeR_plane_norm_x, -eyeR_plane_norm_z, 1, 0],
                    [eyeR_plane_norm_z,  eyeR_plane_norm_x, 0, 1],
                    [eyeL_plane_norm_x, -eyeL_plane_norm_z, 1, 0],
                    [eyeL_plane_norm_z,  eyeL_plane_norm_x, 0, 1]))

# Set photo's X's and Y's
photo_vec = Vector ((eyeR_photo_norm_x,
                     eyeR_photo_norm_z,
                     eyeL_photo_norm_x,
                     eyeL_photo_norm_z))

# compute vertical vector ( s*cos(r), s*sin(r), tx, ty )'
t_vec = plane_mat.inverted() * photo_vec

# Fill in affinity transformation matrix with now known 's*cos(r)', 's*sin(r)', 'tx', 'ty'
t_mat =  Matrix(([t_vec[0], -t_vec[1], t_vec[2]],
                 [t_vec[1],  t_vec[0], t_vec[3]],
                 [0,         0,        1]))


#######################################################################################
### APPLY AFFINE TRANSFORMATION TO UV MAP

# Now we have affine transformation 'T' that for every point on plane locates matching
# point on photo:
# photo_point = T * plane_point
#
# In order to align photo with plane we just need to apply transformation 'T' to plane's UV map
uv_map = photo_plane.data.uv_layers.active

# iterate over UV map
for v in photo_plane.data.loops :
    uv_coord = uv_map.data[v.index].uv # exract UV-coordinate from UV map

    # transform UV coordinate
    uv_tr = t_mat * Vector((uv_coord[0], uv_coord[1], 1))

    uv_coord[0] = uv_tr[0]
    uv_coord[1] = uv_tr[1]
