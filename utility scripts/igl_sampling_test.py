import igl
import numpy as np
import random
from pathlib import Path

import customconfig

system_props = customconfig.Properties('./system.json')

verts, faces = igl.read_triangle_mesh(
    Path(system_props['datasets_path']) / 'data_uni_1000_tee_200527-14-50-42_regen_200612-16-56-43' / 'tee_0BEJ3JZP2O' / 'tee_0BEJ3JZP2O_sim.obj')
num_samples = 5
print(len(faces))

# np.random.seed(601)
for _ in range(3):
    barycentric_samples, face_ids = igl.random_points_on_mesh(num_samples, verts, faces)
    print(face_ids)
    print(barycentric_samples)

    points = np.empty(barycentric_samples.shape)
    for i in range(len(face_ids)):
        face = faces[face_ids[i]]
        barycentric_coords = barycentric_samples[i]
        face_verts = verts[face]
        points[i] = np.dot(barycentric_coords, face_verts)
    print(points)

# for i in range(100):
#     _, face_ids = igl.random_points_on_mesh(num_samples, verts, faces)
#     print(face_ids)
    # for fid in face_ids:
    #     if not ((fid-1) < len(faces) and (fid-1) >= 0):
    #         print('Failed try {} with face {}'.format(i, fid))