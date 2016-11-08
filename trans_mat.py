# PyTest script 
# run with: 'py.test -s trans_mat.py'

import numpy as np

def get_transform(src2, src1, targ2, targ1):
  plane_mat = [[src1[0], -src1[1], 1, 0],
               [src1[1],  src1[0], 0, 1], 
               [src2[0], -src2[1], 1, 0],
               [src2[1],  src2[0], 0, 1]]
  np_plane_mat = np.matrix(plane_mat)

  photo_vec = [[targ1[0]],
               [targ1[1]],
               [targ2[0]],
               [targ2[1]]]
  np_photo_vec = np.matrix(photo_vec)

  t_vec = np_plane_mat.I * np_photo_vec

  t_mat = [[t_vec.item(0), -t_vec.item(1), t_vec.item(2)],
           [t_vec.item(1),  t_vec.item(0), t_vec.item(3)],
           [0,              0,             1]]

  np_t_mat = np.matrix(t_mat)

  #scale_mat = [[1, 0,       0],
  #             [0, scale_y, 0],
  #             [0, 0,       1]]
  #np_scale_mat = np.matrix(scale_mat)

  return np_t_mat




#########################################################
#########################################################
#########################################################
def test_144_vs_069():
  plane_y_to_x = 1.44 # not used

  foto_x_size = 2127  # not used
  foto_y_size = 1477  # not used
  foto_y_to_x = foto_y_size/foto_x_size # 0.6944

  r_plane = [0.3767, 0.5339]
  l_plane = [0.6617, 0.5332]

  r_foto = [0.2539*foto_y_to_x, (0.5762*plane_y_to_x)] # 0.82
  l_foto = [0.4104*foto_y_to_x, (0.5762*plane_y_to_x)]

  print(l_foto)

  trans_mat = get_transform(l_plane, r_plane, l_foto, r_foto)

  uv_vec = [[0, 1, 1, 0], # (1,1)
            [0, 0, 1, 1],
            [1, 1, 1, 1]]
  np_uv_vec = np.matrix(uv_vec)

  uv_t = trans_mat * np_uv_vec
  uv = uv_t.T
  print(uv)

  gt_uv = [[0.0477, 0.0001, 1], # (0,0)
           [0.5970, 0.0028, 1], # (1,0)
           [0.5956, 1.0838, 1], # (1,1)
           [0.0463, 1.0811, 1]] # (0,1)

  assert np.allclose(uv, np.matrix(gt_uv), 1e-03)
  #assert round(uv.item(0), 3) == round(gt_uv[2][0], 3)
  #assert round(uv.item(1), 3) == round(gt_uv[2][1], 3)



###################
def test_144_vs_144():

  plane_y_to_x = 1.44 # not used

  r_plane = [0.3767, 0.5339]
  l_plane = [0.6617, 0.5332]

  r_foto = [0.3899, 0.5762]
  l_foto = [0.7144, 0.5762]

  print(l_foto)

  trans_mat = get_transform(l_plane, r_plane, l_foto, r_foto)
  #trans_mat = get_transform(l_foto, r_foto, l_plane, r_plane)

  uv_mat = np.matrix([[0, 1, 1, 0], # (1,1)
                      [0, 0, 1, 1],
                      [1, 1, 1, 1]])
  uv_mat_t = trans_mat * uv_mat
  print(uv_mat_t.T)

  gt_uv = [[-0.038, -0.033, 1], # (0,0)
           [ 1.101, -0.03,  1], # (1,0)
           [ 1.098,  1.109, 1], # (1,1)
           [-0.04,   1.106, 1]] # (0,1)

  assert np.allclose(uv_mat_t.T, np.matrix(gt_uv), 1e-03, 1e-03)
