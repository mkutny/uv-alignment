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
def match_foto_with_3D (lx, ly, rx, ry, fbx_path, shapekey_eyes_path, location, rotation, scale, plane_AR):

    scene = bpy.context.scene

    # finding eyes object of skinned character
    skinned_eyes_obj = bpy.data.objects["Eyes"]

    # finding plane with photo of character
    photo_plane = scene.objects.get('FotoPlane')

    # finding camera looking at character 
    cam = scene.objects.get('cam')

    # getting size of FotoPlane. 
    # Because origin is in the center, I need sum length in positive and negative direction
    photo_plane_size = 4.71391 * 2 # width/height of the BoyFotoPlane in units (because width=height)

    # import and apply shape key to eyes
    apply_shapekey (shapekey_eyes_path, skinned_eyes_obj)

    # applying skin to eyes
    eyes_obj = convert_skinned_mesh_to_mesh (skinned_eyes_obj)

    # applying character specific transormation to align baked eyes with skinned eyes
    apply_transformations (eyes_obj, location, rotation, scale)

    # Getting world coordinates of 3D eyes' mesh (our landmarks)
    # vertex 192 - center of left eye
    eyeL_3D_world = eyes_obj.matrix_world * eyes_obj.data.vertices[192].co
    # vertex 385 - center of right eye
    eyeR_3D_world = eyes_obj.matrix_world * eyes_obj.data.vertices[385].co 

    # find coordinates on FotoPlane (local space) of 3D mesh landmarks
    eyeL_3D_plane = convert_point3D_to_point2D_w_same_screen_co (eyeL_3D_world, cam, photo_plane)
    eyeR_3D_plane = convert_point3D_to_point2D_w_same_screen_co (eyeR_3D_world, cam, photo_plane)

    # Converting 3D coordinates to 2D point.
    # Because I need only local axis X and Z (Y = 0 for all vertices)
    eyeL_plane = Vector ((eyeL_3D_plane[0], eyeL_3D_plane[2]))
    eyeR_plane = Vector ((eyeR_3D_plane[0], eyeR_3D_plane[2]))

    # Convert plane landmark to UV-coordinates: (0,0) is bottom left, (1,1) is top right
    # Plane origin is located at center and y-axis points down
    eyeL_plane_uv = convert_to_uv (eyeL_plane, photo_plane_size, photo_plane_size, 'CENTER', 'DOWN')
    print ("Left Eye Plane normalized coordinates =", eyeL_plane_uv)

    eyeR_plane_uv = convert_to_uv (eyeR_plane, photo_plane_size, photo_plane_size, 'CENTER', 'DOWN')
    print ("Right Eye Plane normalized coordinates =", eyeR_plane_uv)

    # Get photo landmark coordinates
    # TODO I need to get coordinates of eyesfrom FaceGen or landmarker.io

    # reload Foto file
    bpy.ops.image.reload ()

    # finding width and height of Foto of character
    photo_width = bpy.data.images['Foto'].size[0]   # width of the photo in pixels
    photo_height = bpy.data.images['Foto'].size[1]  # height of the photo in pixels
    photo_AR = photo_height/photo_width             # aspect ration of photo

    # normalizing coordinates of left eye on the photo. 
    # In other words, I'm looking UV coordinates of eyes on foto
    eyeL_photo_uv = convert_to_uv (Vector((lx, ly)), photo_width, photo_height, 'TOPLEFT', 'DOWN')
    print ("Left Eye Foto normalized coordinates =", eyeL_photo_uv)

    # normalizing coordinates of right eye on the photo
    eyeR_photo_uv = convert_to_uv (Vector((rx, ry)), photo_width, photo_height, 'TOPLEFT', 'DOWN')
    print ("Right Eye Foto normalized coordinates =", eyeR_photo_uv)

    # Calculating matrix to transform landmarks on foto to match landmarks on plane
    t_mat = get_affine_matrix (eyeL_plane_uv, eyeR_plane_uv, eyeL_photo_uv, eyeR_photo_uv, photo_AR, plane_AR)

    # Transforming UV of FotoPlane with help of transformation matrix
    transform_UV (t_mat, photo_plane)

    # Exportin FotoPlane with animation to FBX
    export_object_to_FBX (fbx_path, photo_plane)


def apply_shapekey (shapekey_path, ob):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.import_scene.obj(filepath = shapekey_path, use_groups_as_vgroups=False, split_mode='OFF')
    # get list of selected objects
    selected_objects = bpy.context.selected_objects
    bpy.context.scene.objects.active = ob
    selected_objects[0].select = True
    ob.select = True
    # create shapekey for eyes
    bpy.ops.object.join_shapes()
    # set value of last shapekey in list to 1
    bpy.context.active_object.data.shape_keys.key_blocks[-1].value = 1


# apply skin to mesh (bake skin)
def convert_skinned_mesh_to_mesh (skinned_mesh):
    scene = bpy.context.scene
    bpy.ops.object.select_all(action='DESELECT')
    # apply all modifiers (and skin also)
    to_mesh = skinned_mesh.to_mesh (scene, 1, 'RENDER')
    # convert mesh to object
    obj = bpy.data.objects.new ("Baked" + skinned_mesh.name, to_mesh)
    # link object to scene
    scene.objects.link(obj)
    return obj



def apply_transformations (obj, location, rotation, scale):
    # rotate, transform and scale eyes to match skinned
    obj.location = location
    obj.rotation_euler = rotation
    obj.scale = scale
    obj.select = True
    bpy.ops.object.transform_apply (location=True, rotation=True, scale=True)


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
                    # region - part of screen area in Blender; 
                    # rv3d - region that has 3D view (we can see our 3D scene through this region)
                    return region, rv3d
    return None, None


# draw cross at certain position (world coordinates)
def draw_cross (cross_position, message="Drew cross at:", size=1):
    scene = bpy.context.scene
    print(message, cross_position)
    cross = bpy.data.objects.new("Cross", None)
    cross.location = cross_position
    cross.empty_draw_size = size
    scene.objects.link(cross)



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
                draw_cross (intersection, "Intersection found:")
                # print("Intersection found:", intersection)
                # # drawing cross in place of intersection
                # inter = bpy.data.objects.new("Intersection", None)
                # inter.location = intersection
                # inter.empty_draw_size = 2
                # scene.objects.link(inter)

                break # find the first intersection only
        
    return intersection



# find 2D point on plane (local space) corresponding to 3D point (world space) 
# with the same coordinates in screen space of camera
def convert_point3D_to_point2D_w_same_screen_co (point3D, cam, plane):
    scene = bpy.context.scene
    region, rv3d = view3d_find()
    # Find out screen coordinates of 3d point
    point2D_screen = location_3d_to_region_2d(region, rv3d, point3D)
    # print ("point2D in pixels =", point2D_screen)

    # Project RAYS from screen points back to landmarks
    ray_dir = region_2d_to_vector_3d (region, rv3d, point2D_screen) # direction from camera origin to 2D point

    # Find out intersection with plane
    inter = get_intesection (plane, cam.location, ray_dir) # get intersection world coordinates

    # convert coordinates of intersection from world to plane's local
    # local coordinates of plane start in center and have axis X = looking right, Y = 0, Z = looking down
    point2D = plane.matrix_world.inverted() * inter

    return point2D



# get normalized coordinates of 2D point on plane with dimensions: WIDTH and HEIGHT
# origin of coordinates can be CENTER or TOPLEFT
# Y-axis can poit UP or DOWN
# Output value limits from 0,0 to 1,1
def convert_to_uv (point, width, height, origin, y_dir):
    x_orig = point[0]
    y_orig = point[1]

    x_uv = x_orig/width
    y_uv = y_orig/height

    if origin == 'CENTER':
        x_uv = x_uv + 0.5
        y_uv = y_uv + 0.5
    elif origin != 'TOPLEFT':
        print ("Give me correct origin of coordinates: 'CENTER' or 'TOPLEFT'")

    if y_dir == 'DOWN':
        y_uv = 1 - y_uv
    elif y_dir != 'UP':
        print ("Give me correct direction of Y axis: 'UP' or 'DOWN'")

    # TODO Add name of input parameter to print output
    # print ("Normailzed coordinates:", Vector ((point_norm_x, point_norm_y)))

    return Vector ((x_uv, y_uv))




#######################################################################################
### FIND AFFINE TRANSFORMATION (ROTATION, SCALE, TRANSLATION)
def get_affine_matrix(eyeL_plane, eyeR_plane, eyeL_photo, eyeR_photo, photo_ar, plane_ar):
    
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

    # Populate matrix with plane's X's and Y's
    plane_mat = Matrix(([eyeR_plane[0], -eyeR_plane[1], 1, 0],
                        [eyeR_plane[1],  eyeR_plane[0], 0, 1],
                        [eyeL_plane[0], -eyeL_plane[1], 1, 0],
                        [eyeL_plane[1],  eyeL_plane[0], 0, 1]))

    # Set photo's X's and Y's
    photo_vec = Vector ((eyeR_photo[0],
                         eyeR_photo[1],
                         eyeL_photo[0],
                         eyeL_photo[1]))

    # compute vertical vector ( s*cos(r), s*sin(r), tx, ty )'
    t_vec = plane_mat.inverted() * photo_vec

    scale_y = 1 # plane_ar/photo_ar # plane_ar
    print ("scale_y", scale_y)
    # Fill in affinity transformation matrix with now known 's*cos(r)', 's*sin(r)', 'tx', 'ty'
    t_mat =  Matrix(([t_vec[0], -scale_y*t_vec[1], t_vec[2]],
                     [t_vec[1],  scale_y*t_vec[0], t_vec[3]],
                     [0,         0,                1]))

    
    scale_mat = Matrix(([1, 0,       0],
                        [0, 1, 0],
                        [0, 0,       1]))

    return scale_mat * t_mat



#######################################################################################
### APPLY AFFINE TRANSFORMATION TO UV MAP
def transform_UV (affineMatrix, obj):
    scene = bpy.context.scene
    # Now we have affine transformation 'T' that for every point on plane locates matching
    # point on photo:
    # photo_point = T * plane_point
    #
    # In order to align photo with plane we just need to apply transformation 'T' to plane's UV map
    uv_map = obj.data.uv_layers.active

    # iterate over all vertices of UV map
    for v in obj.data.loops :
        uv_coord = uv_map.data[v.index].uv # exract UV-coordinate from UV map

        # transform UV coordinate
        uv_tr = affineMatrix * Vector((uv_coord[0], uv_coord[1], 1))

        uv_coord[0] = uv_tr[0]
        uv_coord[1] = uv_tr[1]


def export_object_to_FBX (fbx_path, obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select = True
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
