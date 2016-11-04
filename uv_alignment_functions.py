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


# transform UV of Girl's FotoPlane based on morphed eyes and coordinates of eyes on photo:
# lx, ly, rx, ry - left eye X, left eye Y, right eye X, right eye Y,
# where X = 0, Y = 0 in the tob left corner of the photo. Y points downwards.
def start (lx, ly, rx, ry, sex):
    obj = skinedMeshToMesh ()
    if sex == 'Girl':
        applyGirlTransformation (obj)
    elif sex == 'Boy':
        applyBoyTransformation (obj)
    else:
        print ("Input correct sex: 'Boy' or 'Girl'.")
    eyeL_3D_world, eyeR_3D_world = getEyes3DWorldCo (obj)
    eyeL_plane_norm, eyeR_plane_norm  = getEyesNormCoPlane (eyeL_3D_world, eyeR_3D_world)
    eyeL_photo_norm, eyeR_photo_norm = getEyesNormCoFoto (lx, ly, rx, ry)
    t_mat = getAffineMatrix (eyeL_plane_norm, eyeR_plane_norm, eyeL_photo_norm, eyeR_photo_norm)
    transformUV (t_mat)
    exportFotoPlaneFBX (sex)



# apply skin to mesh (bake skin)
def skinedMeshToMesh ():
    bpy.ops.object.select_all(action='DESELECT')
    skinned_mesh = bpy.data.objects["Eyes"]
    scene = bpy.context.scene
    # apply all modifiers (and skin also)
    to_mesh = skinned_mesh.to_mesh (scene, 1, 'RENDER')
    # convert mesh to object
    obj = bpy.data.objects.new ("Baked" + skinned_mesh.name, to_mesh)
    # link object to scene
    scene.objects.link(obj)
    return obj



def applyBoyTransformation (obj):
    # rotate and scale eyes to match skinned
    obj.rotation_euler[0] = pi/2
    obj.scale = (0.01, 0.01, 0.01)
    # select eyes
    obj.select = True
    bpy.ops.object.transform_apply (location=True, rotation=True, scale=True)



def applyGirlTransformation (obj):
    # rotate, transform and scale eyes to match skinned
    obj.location = (0.16856, 0.13704, 0.02343)
    obj.rotation_euler = (pi/2, 0, radians (-69.89))
    obj.scale = (0.0085, 0.0085, 0.0085)
    # select eyes
    obj.select = True
    bpy.ops.object.transform_apply (location=True, rotation=True, scale=True)


#######################################################################################
### GETTING WORLD COORDINATES OF 3D MESH LANDMARKS
def getEyes3DWorldCo (eyesObj):
    # getting world coordinates of vertex 192 - center of girl's left eye
    eyeL_3D_world = eyesObj.matrix_world * eyesObj.data.vertices[192].co
    # getting world coordinates of vertex 385 - center of girl's right eye
    eyeR_3D_world = eyesObj.matrix_world * eyesObj.data.vertices[385].co 
    return eyeL_3D_world, eyeR_3D_world




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



# looking for the first intersection of line 
# (line between 2 points: ray_dir and origin)
# and FotoPlane
def get_intesection (ob, origin, ray_dir):
    if None not in (ob, origin, ray_dir) and ob.type == 'MESH':
        scene = bpy.context.scene
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


#######################################################################################
### FIND OUT CORRESPONDING SCREEN COORDINATES
def getEyesNormCoPlane (eyeL_3D_world, eyeR_3D_world):
    scene = bpy.context.scene
    photo_plane = scene.objects.get('FotoPlane')

    #looking for camera location because ray looks from camera location
    camera_origin = scene.objects.get('cam').location

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

    #######################################################################################
    ### FIND OUT INTERSECTION WITH OUR PLANE

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

    print ("Left Eye Plane normalized coordinates = ", eyeL_plane_norm_x, eyeL_plane_norm_z)
    print ("Right Eye Plane normalized coordinates = ", eyeR_plane_norm_x, eyeR_plane_norm_z)
    
    return Vector((eyeL_plane_norm_x, eyeL_plane_norm_z)), Vector((eyeR_plane_norm_x, eyeR_plane_norm_z))



#######################################################################################
### GET PHOTO LANDMARK COORDINATES
# getting coordinates of eyes on photo from FaceGen
def getEyesNormCoFoto(lx, ly, rx, ry):
    # x=0, z=0 are in the left top of the photo.
    # z looking down.
    # I named vertical axis as z because
    # when I'm using local coordinates of BoyFotoPlane I have axis x and z (y = 0 for all vertices).
    eyeL_photo_x = lx       # x position of the left eye on the photo in pixels
    eyeL_photo_z = ly       # z position of the left eye on the photo in pixels

    eyeR_photo_x = rx       # x position of the right eye on the photo in pixels
    eyeR_photo_z = ry       # z position of the right eye on the photo in pixels

    bpy.ops.image.reload ()

    photo_x_size = bpy.data.images['Foto'].size[0]    # width of the photo in pixels
    photo_z_size = bpy.data.images['Foto'].size[1]    # height of the photo in pixels


    #######################################################################################
    ### CONVERT PHOTO COORDS TO UV-SPACE

    # normalizing coordinates of left eye on the photo from pixels to (0,0)-(1,1) and inverting Z axis
    eyeL_photo_norm_x = eyeL_photo_x / photo_x_size
    eyeL_photo_norm_z = 1 - eyeL_photo_z / photo_z_size

    # normalizing coordinates of right eye on the photo from pixels to (0,0)-(1,1) and inverting Z axis
    eyeR_photo_norm_x = eyeR_photo_x / photo_x_size
    eyeR_photo_norm_z = 1 - eyeR_photo_z / photo_z_size

    print ("Left Eye Foto normalized coordinates = ", eyeL_photo_norm_x, eyeL_photo_norm_z)
    print ("Right Eye Foto normalized coordinates = ", eyeR_photo_norm_x, eyeR_photo_norm_z)
    

    return Vector((eyeL_photo_norm_x, eyeL_photo_norm_z)), Vector((eyeR_photo_norm_x, eyeR_photo_norm_z))



#######################################################################################
### FIND AFFINE TRANSFORMATION (ROTATION, SCALE, TRANSLATION)
def getAffineMatrix(eyeL_plane_norm, eyeR_plane_norm, eyeL_photo_norm, eyeR_photo_norm):
    
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
    plane_mat = Matrix(([eyeR_plane_norm[0], -eyeR_plane_norm[1], 1, 0],
                        [eyeR_plane_norm[1],  eyeR_plane_norm[0], 0, 1],
                        [eyeL_plane_norm[0], -eyeL_plane_norm[1], 1, 0],
                        [eyeL_plane_norm[1],  eyeL_plane_norm[0], 0, 1]))

    # Set photo's X's and Y's
    photo_vec = Vector ((eyeR_photo_norm[0],
                         eyeR_photo_norm[1],
                         eyeL_photo_norm[0],
                         eyeL_photo_norm[1]))

    # compute vertical vector ( s*cos(r), s*sin(r), tx, ty )'
    t_vec = plane_mat.inverted() * photo_vec

    # Fill in affinity transformation matrix with now known 's*cos(r)', 's*sin(r)', 'tx', 'ty'
    t_mat =  Matrix(([t_vec[0], -t_vec[1], t_vec[2]],
                     [t_vec[1],  t_vec[0], t_vec[3]],
                     [0,         0,        1]))
    return t_mat



#######################################################################################
### APPLY AFFINE TRANSFORMATION TO UV MAP
def transformUV (affineMatrix):
    scene = bpy.context.scene
    photo_plane = scene.objects.get('FotoPlane')
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
        uv_tr = affineMatrix * Vector((uv_coord[0], uv_coord[1], 1))

        uv_coord[0] = uv_tr[0]
        uv_coord[1] = uv_tr[1]


def exportFotoPlaneFBX(sex):
    fbx_path = "d:\desktop\Matching-Photo-n-3D-4UE\sc01_sh0030_{0}FotoPlane_transfUV.fbx".format(sex)
    scene = bpy.context.scene
    photo_plane = scene.objects.get('FotoPlane')
    bpy.ops.object.select_all(action='DESELECT')
    photo_plane.select = True
    bpy.ops.export_scene.fbx (filepath=fbx_path, check_existing=False, axis_forward='-Z', axis_up='Y',
                    filter_glob="*.fbx", version='BIN7400', ui_tab='MAIN', use_selection=True,
                    global_scale=1.0, apply_unit_scale=True, bake_space_transform=False,
                    object_types={'MESH'}, use_custom_props=False, path_mode='AUTO', batch_mode='OFF',
                    use_mesh_modifiers=True, mesh_smooth_type='OFF', use_mesh_edges=False,
                    use_tspace=False, use_armature_deform_only=True, add_leaf_bones=True,
                    primary_bone_axis='Y', secondary_bone_axis='X', armature_nodetype='NULL',
                    bake_anim=True, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=False,
                    bake_anim_use_all_actions=False, bake_anim_force_startend_keying=False, 
                    bake_anim_step=1.0, bake_anim_simplify_factor=0,
                    use_anim=True, use_anim_action_all=True, use_default_take=True,
                    use_anim_optimize=True, anim_optimize_precision=6.0,  embed_textures=False, 
                    use_batch_own_dir=False, use_metadata=True)