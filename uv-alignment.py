import bpy, bmesh
from mathutils import Vector, Matrix
from mathutils.geometry import intersect_ray_tri
from bpy_extras.view3d_utils import region_2d_to_vector_3d
from bpy_extras.view3d_utils import location_3d_to_region_2d
from math import cos, sin

# todo
# 1.1. move timeslider to 336 frame for boy
# 1.2. find screen coordinates of 3D eyes
# 1.3. find intersections of ray from 3D eyes with BoyFotoPlane (in local coordinates of BoyFotoPlane)

# 2.1. find distances: 1.between eyes; 2. between eyes' line and mouth
# 2.2. scale uv horiz (to match distance between eyes). Anchor - left eye
# 2.3. scale uv vertical (to match distance between eye's line and mouth). Anchor - left eye

# 3.1. find angle between 3D eyes in screen coordinates (in pixels)
# 3.2. find angle between eye's line and horizontal axis on the photo
# 3.3. find difference between 1.1 and 1.2 and rotate uv for this value
# 3.4. find new coordinates of eyes on photo (after uv rotation)

# 2.3. compare distances between 3d and photo for eyes and mouth
# 6. move uv

#######################################################################################
################################## 1.2 ################################################
#######################################################################################

scene = bpy.context.scene # getting current scene

# looking for 3d view. It MUST be one with Camera as main camera
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

# looking for position of 4 points of camera borders in screen coordinates (in pixels).
# 0,0 - left bottom corner of 3dview region.
def view3d_camera_border(scene):
    obj = scene.camera
    cam = obj.data
    
    frame = cam.view_frame(scene)

    # move into object space
    frame = [obj.matrix_world * v for v in frame]

    # move into pixelspace
    region, rv3d = view3d_find()
    frame_px = [location_3d_to_region_2d(region, rv3d, v) for v in frame]

    return frame_px

frame_px = view3d_camera_border(bpy.context.scene)

region, rv3d = view3d_find()

#getting world coordinates of vertex 29478 in the center of left eye
eyeL3D_wco = bpy.data.objects["BoyMorphed"].matrix_world*bpy.data.objects["BoyMorphed"].data.vertices[29478].co 
#getting world coordinates of vertex 29783 in the center of right eye
eyeR3D_wco = bpy.data.objects["BoyMorphed"].matrix_world*bpy.data.objects["BoyMorphed"].data.vertices[29783].co 

# looking for position of eyes and mouth in screeen coordinates (in pixels). 0,0 - left bottom corner of 3dview region
eyeL3D_px = location_3d_to_region_2d(region, rv3d, eyeL3D_wco)
eyeR3D_px = location_3d_to_region_2d(region, rv3d, eyeR3D_wco)

#######################################################################################
################################## 1.3 ################################################
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

# convert coordinates of intersection from world to FotoPlane's local
interEyeL_local = BoyFotoPlane.matrix_world.inverted()*interEyeL
interEyeR_local = BoyFotoPlane.matrix_world.inverted()*interEyeR

photoPlaneSize = 4.71391 # half width/height of the BoyFotoPlane in units (because width=height)

# normalizing coordinates of left eye intersection from local to range 0,0-1,1
interEyeL_co_nx = ((interEyeL_local[0] + photoPlaneSize)/(photoPlaneSize))/2
interEyeL_co_nz = ((interEyeL_local[2] + photoPlaneSize)/(photoPlaneSize))/2

# normalizing coordinates of right eye intersection from local to range 0,0-1,1
interEyeR_co_nx = ((interEyeR_local[0] + photoPlaneSize)/(photoPlaneSize))/2
interEyeR_co_nz = ((interEyeR_local[2] + photoPlaneSize)/(photoPlaneSize))/2

print ("Right Eye Plane =", interEyeR_co_nx, interEyeR_co_nz)
print ("Left Eye Plane =", interEyeL_co_nx, interEyeL_co_nz)

#######################################################################################
################################## 3.2 ################################################
#######################################################################################

# x=0, z=0 are in the center of the photo.
# z looking down.
# I named vertical axis as z because
# when I'm using local coordinates of FotoPlane I have axis x and z (y = 0 for all vertices).
eyeL_photo_x = 89 # x position of the left eye on the photo in pixels
eyeL_photo_z = -219 # z position of the left eye on the photo in pixels

eyeR_photo_x = -198 # x position of the right eye on the photo in pixels
eyeR_photo_z = -176 # z position of the right eye on the photo in pixels

photo_x = 382 # half width of the photo in pixels
photo_z = 512 # half height of the photo in pixels

ar = 1.44151 # aspect ratio of BoyFotoPlane

# normalizing coordinates of left eye on the photo from pixels to 0,0-1,1
eyeL_foto_co_nx = ((eyeL_photo_x + photo_x)/(photo_x))/2
eyeL_foto_co_nz = ((eyeL_photo_z + photo_z)/(photo_z))/2

# normalizing coordinates of right eye on the photo from pixels to 0,0-1,1
eyeR_foto_co_nx = ((eyeR_photo_x + photo_x)/(photo_x))/2
eyeR_foto_co_nz = ((eyeR_photo_z + photo_z)/(photo_z))/2

print ("Right Eye Foto =", eyeR_foto_co_nx, eyeR_foto_co_nz)
print ("Left Eye Foto =", eyeL_foto_co_nx, eyeL_foto_co_nz)

#######################################################################################
################################## 3.2 ################################################
#######################################################################################

# distance between intersections of 3D eyes on BoyFotoPlane 
dist_btw_interEyes = (Vector((interEyeL_co_nx, interEyeL_co_nz)) - Vector((interEyeR_co_nx, interEyeR_co_nz))).length
#print ("dist_btw_interEyes =", dist_btw_interEyes)

# distance between eyes on BoyFotoPlane
# TODO
# MAYBE I need to take into account real scale of foto (because uv is square but foto is rectangle)
dist_btw_eyes_foto = (Vector((eyeL_foto_co_nx, eyeL_foto_co_nz)) - Vector((eyeR_foto_co_nx, eyeR_foto_co_nz))).length
#print ("dist_btw_eyes_foto =", dist_btw_eyes_foto)

# difference between eyes' distances (between photo and 3D)
diff_eyes_dist = dist_btw_interEyes - dist_btw_eyes_foto + 1
#print ("diff_eyes_dist =", diff_eyes_dist)

#######################################################################################
################################## 1.2 ################################################
#######################################################################################

# looking for tilt of 3D eyes in screen coordinates
eyes3D_vec = eyeL3D_px - eyeR3D_px
eyes3D_angle =  eyes3D_vec.angle_signed (((1, 0)), None)
#print ("eyes3D_angle =", eyes3D_angle)



# looking for tilt of eyes on photo: angle between eyes' line and x axis
eyes_vec = Vector ((eyeL_photo_x, eyeL_photo_z)) - Vector ((eyeR_photo_x, eyeR_photo_z))
eyes_angle =  eyes_vec.angle_signed (((1, 0)), None)
#print ("eyes_angle =", eyes_angle)


# substracting tilt of 3D eyes from tilt of eyes on photo
eyes_angle_dif = eyes_angle + eyes3D_angle

#######################################################################################
################################## 4.1 ################################################
#######################################################################################

# Translation

# difference between intersection and real left eye location on photo
diff_x = interEyeL_co_nx - eyeL_foto_co_nx
diff_z = interEyeL_co_nz - eyeL_foto_co_nz
#print (diff_x)
#print (diff_z)

matrixT = Matrix.Translation ((1,2,3)).to_3x3 ()
'''matrixT[0][0] = diff_eyes_dist*cos(eyes_angle_dif)
matrixT[0][1] = -diff_eyes_dist*sin(eyes_angle_dif)
matrixT[0][2] = diff_x

matrixT[1][0] = diff_eyes_dist*sin(eyes_angle_dif)
matrixT[1][1] = diff_eyes_dist*cos(eyes_angle_dif)
matrixT[1][2] = diff_z'''

matrixT[0][0] = 1.3215652476201316
matrixT[0][1] = -0.14416606659672285
matrixT[0][2] = -0.19056776666193095

matrixT[1][0] = 0.14416606659672285
matrixT[1][1] = 1.3215652476201316
matrixT[1][2] = 0.0011849421378985652

matrixT[2][0] = 0
matrixT[2][1] = 0
matrixT[2][2] = 1



#print (matrixT)

# scaling uv
UVmap = BoyFotoPlane.data.uv_layers.active
for v in BoyFotoPlane.data.loops :
    uv_vec = UVmap.data[v.index].uv # uv vector

    uv_x = uv_vec[0] # x coord
    uv_y = uv_vec[1] # y coord

    uv_tr = matrixT * Vector(uv_x, uv_y, 1) # transformed vector

    uv[0] = uv_tr[0]
    uv[1] = uv_tr[1]

#######################################################################################
################################## 5.1 ################################################
#######################################################################################


