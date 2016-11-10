# PyTest script 
# run with: 'py.test -s -v trans_mat.py'

import numpy as np
import pytest

# return transformation and its decomposition on scale, rotation, translation
def get_transform(src2, src1, targ2, targ1):
  source_mat = np.matrix([[src1[0], -src1[1], 1, 0],
                         [src1[1],  src1[0], 0, 1], 
                         [src2[0], -src2[1], 1, 0],
                         [src2[1],  src2[0], 0, 1]])

  target_vec = np.matrix([[targ1[0]],
                         [targ1[1]],
                         [targ2[0]],
                         [targ2[1]]])

  # Solve SOURCE * t_vec = TARGET
  # t_vec = [s*cos, s*sin, trans_x, trans_y]
  t_vec = source_mat.I * target_vec

  # combine transformation matrix
  t_mat = np.matrix([[t_vec.item(0), -t_vec.item(1), t_vec.item(2)],
                     [t_vec.item(1),  t_vec.item(0), t_vec.item(3)],
                     [0,              0,             1]])

  # derive translation
  translation = np.matrix([[t_vec.item(2)], [t_vec.item(3)]])

  # derive scale
  scale_x = np.linalg.norm(np.matrix([t_vec.item(0), t_vec.item(1)]))
  scale_y = np.linalg.norm(np.matrix([t_vec.item(0), t_vec.item(1)]))
  scale = np.matrix([[scale_x, 0,       0],
                     [0,       scale_y, 0],
                     [0,       0,       1]])

  # derive rotation
  rotation = np.matrix([[t_vec.item(0)/scale_x, -t_vec.item(1)/scale_y, 0],
                        [t_vec.item(1)/scale_x,  t_vec.item(0)/scale_y, 0],
                        [0,                      0,                     1]])
  return t_mat, scale, rotation, translation


# helper function to get 3x3 Scale matrix
def get_scale_mat(scale_x, scale_y):
  return np.matrix([[scale_x, 0,       0],
                    [0,       scale_y, 0],
                    [0,       0,       1]])


#########################################################
### UNIT TESTS
#########################################################
@pytest.fixture(scope="function",
                params=[
                  (# plane y/x: 1.44, photo y/x: 1.44, rotation: 0
                   1, # photo_x_size
                   1.44, # photo_y_size
                   [0.3899, 0.5762*1.44], # photo right x,y
                   [0.7144, 0.5762*1.44], # photo left x,y
                   # (expected result (ground truth)
                   [[-0.03590792, -0.03274251, 1], # (0,0)
                    [ 1.10267433, -0.02994599, 1], # (1,0)
                    [ 1.09687547,  1.10863626, 1], # (1,1)
                    [-0.04170678,  1.10583974, 1]] # (0,1)
                  ),

                  (# plane y/x: 1.44, photo y/x: 0.6944, rotation: 0
                   2127, # photo_x_size
                   1477, # photo_y_size
                   [540, 851], # photo right x,y
                   [873, 851], # photo left x,y
                   # (expected result (ground truth)
                   [[0.04844307, -0.03307127, 1], # (0,0)
                    [0.59776438, -0.03027339, 1], # (1,0)
                    [0.59496666,  1.10886356, 1], # (1,1)
                    [0.04564534,  1.10606568, 1]] # (0,1)
                  ),

                  (# plane y/x: 1.44, photo y/x: 1.44, rotation: 45deg CCW
                   764, # photo_x_size
                   1110, # photo_y_size
                   [345, 1100-490], # photo right x,y
                   [559, 1100-294], # photo left x,y
                   # (expected result (ground truth)
                   [[ 0.77726320, -0.20312630, 1], # (0,0)
                    [ 1.75689079,  0.41882541, 1], # (1,0)
                    [ 0.45567664,  1.38976873, 1], # (1,1)
                    [-0.52395095,  0.76781702, 1]] # (0,1)),
                  )
                 ], # end of params
                 ids=["1.44 vs 1.44 rotation 0", "1.44 vs 0.69, rotation 0", "144_vs_144_45deg"]
                )
def prepare_fixture(request):
  plane_x_size = 4.71391*2
  plane_y_size = plane_x_size * 1.44
  # normalized (0-1) coords
  r_plane = [0.3767*plane_x_size, 0.5339*plane_y_size]
  l_plane = [0.6617*plane_x_size, 0.5332*plane_y_size]
  # retun combined tuple
  return (plane_x_size, plane_y_size, r_plane, l_plane) + request.param


def test_alignment(prepare_fixture):
  # setting initial parameters from the fixture
  (plane_x_size, plane_y_size, r_plane, l_plane, photo_x_size, photo_y_size, r_photo, l_photo, gt_uv_map) = prepare_fixture
  
  # Calculate transformation matrix, which transforms plane points to match photo points
  trans_mat, scale, rotation, translation = get_transform(l_plane, r_plane, l_photo, r_photo)
  #print("scale:\n", scale)
  #print("rotation:\n", rotation)
  #print("translation:\n", translation)
  #print("transformation:\n", trans_mat)


  # UV-grid is normilized, so that bottom left is (0,0) and top right is (1,1).
  uv_map = np.matrix([#00 10 11 01
                      [0, 1, 1, 0],
                      [0, 0, 1, 1],
                      [1, 1, 1, 1]])

  # UV-grid needs to be normilized but the plane and photo are not squares.
  # Therefore we need to:
  # 1. Scale UV-map to match the plane's scale
  # 2. Apply transformation to UV-map. Now uv-map is in photo's coordinate frame)
  # 3. Scale UV-map in photo coordinate frame back to (0,0):(1,1)
  
  # 1. Scale UV-map to match plane's coord frame (1.44:1)
  uv_scale_mat = get_scale_mat(plane_x_size, plane_y_size)

  # 3. calculate scale-back matrix for photo frame
  scale_back_mat = get_scale_mat(1/photo_x_size, 1/photo_y_size)

  # 2. Apply
  uv_map_transf = scale_back_mat * trans_mat * uv_scale_mat * uv_map

  #print("Calculated UV map:\n", uv_map_transf.T)
  assert np.allclose(uv_map_transf.T, np.matrix(gt_uv_map), 1e-01, 1e-03)
