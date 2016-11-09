# PyTest script 
# run with: 'py.test -s trans_mat.py'

import numpy as np

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
  plane_y_scale = 1.44
  plane_scale_mat = np.matrix([[1, 0,             0],
                               [0, plane_y_scale, 0],
                               [0, 0,             1]])
  photo_scale_mat = np.matrix([[1, 0,             0],
                               [0, 1/photo_y_scale, 0],
                               [0, 0,             1]])
  rescale_mat = np.matrix([[1,          0,                0],
                           [0,          1/photo_y_scale,  0],
                           [0,          0,                1]])
  return rescale_mat



#########################################################
#########################################################
#########################################################
def test_144_vs_069():
  plane_y_to_x = 1.44 # not used

  photo_x_size = 2127
  photo_y_size = 1477
  photo_y_scale = photo_y_size/photo_x_size # 0.6944

  r_plane = [0.3767, 0.5339]
  l_plane = [0.6617, 0.5332]

  r_foto = [540/photo_x_size, 851/photo_y_size*photo_y_scale]
  l_foto = [873/photo_x_size, 851/photo_y_size*photo_y_scale]

  trans_mat, scale, rotation, translation = get_transform(l_foto, r_foto, l_plane, r_plane)
  #print("scale:\n", scale)
  #print("rotation:\n", rotation)
  #print("translation:\n", translation)
  #print("transformation:\n", trans_mat)
  scale_back_mat = get_rescale(photo_y_scale)

  uv_vec = np.matrix([[0, 1, 1, 0], # (1,1)
                      [0, 0, 1.44, 1.44],
                      [1, 1, 1, 1]])

  uv_mat_t = trans_mat * uv_vec
  uv_mat_rescaled_back = scale_back_mat * uv_mat_t
  print("original transform 1.44 vs 0.69:\n", uv_mat_t.T)
  print("scaled back transform 1.44 vs 0.69:\n", uv_mat_rescaled_back.T)

  gt_uv = [[0.0477, 0.0001, 1], # (0,0)
           [0.5970, 0.0028, 1], # (1,0)
           [0.5956, 1.0838, 1], # (1,1)
           [0.0463, 1.0811, 1]] # (0,1)

  #assert np.allclose(uv_mat_t.T, np.matrix(gt_uv), 1e-03, 1e-03)



###################
def test_144_vs_144():

  plane_y_to_x = 1.44 # not used

  r_plane = [0.3767, 0.5339]
  l_plane = [0.6617, 0.5332]

  r_foto = [0.3899, 0.5762]
  l_foto = [0.7144, 0.5762]

  trans_mat, scale, rotation, translation = get_transform(l_plane, r_plane, l_foto, r_foto)
  #print("scale:\n", scale)
  #print("rotation:\n", rotation)
  #print("translation:\n", translation)
  #print("transformation:\n", trans_mat)

  uv_mat = np.matrix([#00 10 11 01
                      [0, 1, 1, 0],
                      [0, 0, 1.44, 1.44],
                      [1, 1, 1, 1]])
  scale_back_mat = np.matrix([[1, 0,      0],
                              [0, 0.6944444444, 0],
                              [0, 0,      1]])
  uv_mat_t = trans_mat * uv_mat
  uv_mat_rescaled_back = scale_back_mat * uv_mat_t
  #print("1.44 vs 1.44:\n", uv_mat_t.T)
  #print("uv rescaled back:\n", uv_mat_rescaled_back.T)

  gt_uv = [[-0.038, -0.033, 1], # (0,0)
           [ 1.101, -0.03,  1], # (1,0)
           [ 1.098,  1.109, 1], # (1,1)
           [-0.040,  1.106, 1]] # (0,1)

  #assert np.allclose(uv_mat_t.T, np.matrix(gt_uv), 1e-03, 1e-03)




###################
def test_144_vs_144_45deg():

  plane_y_scale = 1.44

  photo_x_size = 764
  photo_y_size = 1110
  photo_y_scale = photo_y_size/photo_x_size # 1.44


  r_plane = [0.3767, 0.5339*plane_y_scale]
  l_plane = [0.6617, 0.5332*plane_y_scale]

  r_foto_abs = [345, photo_y_size - 490]
  l_foto_abs = [559, photo_y_size - 294]

  r_foto = [345/photo_x_size, (photo_y_size - 490)/photo_y_size*photo_y_scale]
  l_foto = [559/photo_x_size, (photo_y_size - 294)/photo_y_size*photo_y_scale]

  trans_mat, scale, rotation, translation = get_transform(l_plane, r_plane, l_foto, r_foto)
  #print("scale:\n", scale)
  #print("rotation:\n", rotation)
  #print("translation:\n", translation)
  #print("transformation:\n", trans_mat)

  uv_mat = np.matrix([#00 10 11 01
                      [0, 1, 1, 0],
                      [0, 0, 1.44, 1.44],
                      [1, 1, 1, 1]])
  scale_back_mat = np.matrix([[1, 0,      0],
                              [0, 0.6944444444, 0],
                              [0, 0,      1]])
  uv_mat_t = trans_mat * uv_mat
  uv_mat_rescaled_back = scale_back_mat * uv_mat_t
  #print("1.44 vs 1.44:\n", uv_mat_t.T)
  #print("uv rescaled back:\n", uv_mat_rescaled_back.T)
  gt_uv = [[ 0.781, -0.217, 1], # (0,0)
           [ 1.777,  0.423, 1], # (1,0)
           [ 0.443,  1.414, 1], # (1,1)
           [-0.552,  0.774, 1]] # (0,1)

  #assert np.allclose(uv_mat_t.T, np.matrix(gt_uv), 1e-03, 1e-03)



#### solving 1.44:1.44
#solve = get_transform([0, 0], [1, 1], [-0.038, -0.033], [1.098,  1.109])
#print("solving 1.44:1.44 for (0,0) & (1,1):\n", solve, "\n")

#solve = get_transform([1, 0], [0, 1], [1.101, -0.030], [-0.040,  1.106])
#print("solving 1.44:1.44 for (1,0) & (0,1):\n", solve, "\n")
#print()

# solving 1.44:0.69
#solve = get_transform([0, 0], [1, 1], [0.0477, 0.0001], [0.5956, 1.0838])
#print("solving 1.44:0.69 for (0,0) & (1,1):\n", solve, "\n")

#solve = get_transform([1, 0], [0, 1], [0.5970, 0.0028], [0.0463, 1.0811])
#print("solving 1.44:0.69 for (1,0) & (0,1):\n", solve, "\n")

