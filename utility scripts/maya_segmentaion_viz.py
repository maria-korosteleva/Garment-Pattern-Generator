"""
    Visualize mesh with segmentation lables.
    Tiny script to be executed within Maya Python environemnt. 
    Primaily designed for debug purposes
"""

import os
import numpy as np
import time

# Maya
import maya.cmds as cmds

# My 
from mayaqltools import utils

# setup
obj_path = 'C:/Users/Asus/Desktop/Garments_outs/segment/skirt_210517-15-43-07/skirt_8_panels_sim.obj'
segmentation_path = 'C:/Users/Asus/Desktop/Garments_outs/segment/skirt_210517-15-43-07/skirt_8_panels_simsegmentation.txt'

# load geometry
garment = utils.load_file(os.path.join(obj_path))
num_verts = cmds.polyEvaluate(garment, vertex=True)

# load labels
with open(segmentation_path, 'r') as f:
    vert_labels = [line for line in f]

unique_labels = list(set(vert_labels))  # all unique labels available

# Coloring vertices for visualization
# https://www.schemecolor.com/bright-rainbow-colors.php
color_hex = ['FF0900', 'FF7F00', 'FFEF00', '00F11D', '0079FF', 'A800FF']
color_list = np.empty((len(color_hex), 3))
for idx in range(len(color_hex)):
    color_list[idx] = np.array([int(color_hex[idx][i:i + 2], 16) for i in (0, 2, 4)]) / 255.0

start_time = time.time()
for i in range(num_verts):
    # Color according to evaluated label!
    str_label = vert_labels[i]

    if str_label is None or 'None' in str_label:  # non-segmented becomes black
        color = np.zeros(3)
    else:
        label = unique_labels.index(str_label)

        # color selection with expnasion if the list is too small
        factor, color_id = (label // len(color_list)) + 1, label % len(color_list)
        color = color_list[color_id] / factor  # gets darker the more labels there are

    cmds.polyColorPerVertex(garment + '.vtx[%d]' % i, rgb=color.tolist())

cmds.setAttr(garment + '.displayColors', 1)
cmds.refresh()
print('Colorization: ', time.time() - start_time)
