# PyTest script 
# run with: 'py.test -s trans_mat.py'

import numpy as np
import pytest

def get_transform(src2, src1, targ2, targ1):
  plane_mat = np.matrix([[src1[0], -src1[1], 1, 0],
                         [src1[1],  src1[0], 0, 1], 
                         [src2[0], -src2[1], 1, 0],
                         [src2[1],  src2[0], 0, 1]])

  photo_vec = np.matrix([[targ1[0]],
                         [targ1[1]],
                         [targ2[0]],
                         [targ2[1]]])

  t_vec = plane_mat.I * photo_vec

  t_mat = np.matrix([[t_vec.item(0), -t_vec.item(1), t_vec.item(2)],
                     [t_vec.item(1),  t_vec.item(0), t_vec.item(3)],
                     [0,              0,             1]])

  translation = np.matrix([[t_vec.item(2)], [t_vec.item(3)]])
  scale_x = np.linalg.norm(np.matrix([t_vec.item(0), t_vec.item(1)]))
  scale_y = np.linalg.norm(np.matrix([t_vec.item(0), t_vec.item(1)]))
  scale = np.matrix([[scale_x, 0,       0],
                     [0,       scale_y, 0],
                     [0,       0,       1]])
  rotation = np.matrix([[t_vec.item(0)/scale_x, -t_vec.item(1)/scale_y, 0],
                        [t_vec.item(1)/scale_x,  t_vec.item(0)/scale_y, 0],
                        [0,                      0,                     1]])
  return t_mat, scale, rotation, translation


def get_rescale(photo_y_scale):
  rescale_mat = np.matrix([[1,          0,                0],
                           [0,          1/photo_y_scale,  0],
                           [0,          0,                1]])
  return rescale_mat



#########################################################
#########################################################
#########################################################




###################
def test_144_vs_144():

  plane_y_scale = 1.44 # not used
  photo_y_scale = 1.44
  r_plane = [0.3767, 0.5339*plane_y_scale]
  l_plane = [0.6617, 0.5332*plane_y_scale]

  r_foto = [0.3899, 0.5762*photo_y_scale]
  l_foto = [0.7144, 0.5762*photo_y_scale]

  trans_mat, scale, rotation, translation = get_transform(l_plane, r_plane, l_foto, r_foto)
  #print("scale:\n", scale)
  #print("rotation:\n", rotation)
  #print("translation:\n", translation)
  #print("transformation:\n", trans_mat)

  uv_mat = np.matrix([#00 10 11 01
                      [0, 1, 1, 0],
                      [0, 0, 1.44, 1.44],
                      [1, 1, 1, 1]])
  scale_back_mat = get_rescale(photo_y_scale)
  
  uv_mat_t = scale_back_mat * trans_mat * uv_mat
  #print("1.44 vs 1.44:\n", uv_mat_t.T)

  gt_uv = [[-0.038, -0.033, 1], # (0,0)
           [ 1.101, -0.03,  1], # (1,0)
           [ 1.098,  1.109, 1], # (1,1)
           [-0.040,  1.106, 1]] # (0,1)

  assert np.allclose(uv_mat_t.T, np.matrix(gt_uv), 1e-02, 1e-02)







def test_144_vs_069():
  plane_y_scale = 1.44 # not used

  photo_x_size = 2127
  photo_y_size = 1477
  photo_y_scale = photo_y_size/photo_x_size # 0.6944

  r_plane = [0.3767, 0.5339*plane_y_scale]
  l_plane = [0.6617, 0.5332*plane_y_scale]

  r_foto = [540/photo_x_size, 851/photo_y_size*photo_y_scale]
  l_foto = [873/photo_x_size, 851/photo_y_size*photo_y_scale]

  trans_mat, scale, rotation, translation = get_transform(l_plane, r_plane, l_foto, r_foto)
  #print("scale:\n", scale)
  #print("rotation:\n", rotation)
  #print("translation:\n", translation)
  #print("transformation:\n", trans_mat)

  uv_vec = np.matrix([[0, 1, 1, 0], # (1,1)
                      [0, 0, 1.44, 1.44],
                      [1, 1, 1, 1]])
  scale_back_mat = get_rescale(photo_y_scale)

  uv_mat_t = scale_back_mat * trans_mat * uv_vec
  #print("original transform 1.44 vs 0.69:\n", uv_mat_t.T)

  gt_uv = [[0.0477, 0.0001, 1], # (0,0)
           [0.5970, 0.0028, 1], # (1,0)
           [0.5956, 1.0838, 1], # (1,1)
           [0.0463, 1.0811, 1]] # (0,1)

  assert np.allclose(uv_mat_t.T, np.matrix(gt_uv), 1e-01, 1e-01)





@pytest.fixture(scope="function", params=[
(# plane y/x: 1.44, photo y/x: 0.6944, rotation: 0
 2127, # photo_x_size
 1477, # photo_y_size
 [540, 851], # photo right x,y
 [873, 851], # photo left x,y
 # (expected result (ground truth)
 [[0.0477, 0.0001, 1], # (0,0)
  [0.5970, 0.0028, 1], # (1,0)
  [0.5956, 1.0838, 1], # (1,1)
  [0.0463, 1.0811, 1]] # (0,1)
),

(# plane y/x: 1.44, photo y/x: 1.44, rotation: 45deg CCW
 764, # photo_x_size
 1110, # photo_y_size
 [345, 764-490], # photo right x,y
 [559, 1100-294], # photo left x,y
 # (expected result (ground truth)
 [[ 0.781, -0.217, 1], # (0,0)
  [ 1.777,  0.423, 1], # (1,0)
  [ 0.443,  1.414, 1], # (1,1)
  [-0.552,  0.774, 1]] # (0,1)),
)
],
ids=["1.44 vs 0.69, rotation 0", "144_vs_144_45deg"]
)
def prepare_fixture(request):
  plane_y_scale = 1.44
  r_plane = [0.3767, 0.5339*plane_y_scale]
  l_plane = [0.6617, 0.5332*plane_y_scale]
  return (plane_y_scale, r_plane, l_plane) + request.param


def test_alignment(prepare_fixture):
  # setting initial parameters
  (plane_y_scale, r_plane, l_plane, photo_x_size, photo_y_size, r_photo_abs, l_photo_abs, gt_uv) = prepare_fixture

  photo_y_scale = photo_y_size/photo_x_size

  r_foto = [r_photo_abs[0]/photo_x_size, (photo_y_size - 490)/photo_x_size]
  l_foto = [l_photo_abs[0]/photo_x_size, (photo_y_size - 294)/photo_x_size]
  
  trans_mat, scale, rotation, translation = get_transform(l_plane, r_plane, l_foto, r_foto)
  #print("scale:\n", scale)
  #print("rotation:\n", rotation)
  #print("translation:\n", translation)
  #print("transformation:\n", trans_mat)

  uv_mat = np.matrix([#00 10 11 01
                      [0, 1, 1, 0],
                      [0, 0, 1.44, 1.44],
                      [1, 1, 1, 1]])

  scale_back_mat = get_rescale(photo_y_scale)
  uv_mat_t = scale_back_mat * trans_mat * uv_mat

  #print("1.44 vs 1.44:\n", uv_mat_t.T)
  assert np.allclose(uv_mat_t.T, np.matrix(gt_uv), 1e-01, 1e-01)
