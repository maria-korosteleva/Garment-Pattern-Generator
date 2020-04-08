"""
    Module to batch-simulate garments from patterns in Maya.
    Note that Maya uses Python 2.7 (incl Maya 2020) hence this module is adapted to Python 2.7
"""
# Basic
from __future__ import print_function
import json
from os import path
import numpy as np

# Maya
from maya import cmds

# My module
from pattern.core import BasicPattern


class MayaPattern(BasicPattern):
    """
    Extends a pattern specification in custom JSON format to work with Maya
        Input:
            * Pattern template in custom JSON format
        * import panel to Maya scene TODO
        * cleaning imported stuff TODO
        * Basic operations on panels in Maya TODO
    """
    def __init__(self, pattern_file):
        super(MayaPattern, self).__init__(pattern_file)
    
    def load(self):
        """
            Loads current pattern to Maya as curve collection.
            Groups them by panel and by pattern
        """
        maya_panel_names = []
        for panel_name in self.pattern['panels']:
            maya_panel_names.append(self._load_panel(panel_name))
        group_name = cmds.group(maya_panel_names, n=self.name)
        self.pattern['maya'] = group_name  # Maya modifies specified name for uniquness
        
        print("All panels loaded to Maya")

    def _load_panel(self, panel_name):
        """
            Loads curves contituting given panel to Maya. 
            Goups them per panel
        """
        panel = self.pattern['panels'][panel_name]
        vertices = np.asarray(panel['vertices'])
        # to 3D
        vertices = np.c_[vertices, np.zeros(len(panel['vertices']))]

        curve_names = []
        # now draw edges
        for edge in panel['edges']:
            curve_points = self._edge_as_3d_tuple_list(edge, vertices)            
            curve = cmds.curve(p=curve_points, d=(len(curve_points) - 1))
            curve_names.append(curve)
            edge['maya'] = curve
        
        group_name = cmds.group(curve_names, n=panel_name)
        panel['maya'] = group_name  # Maya modifies specified name for uniquness
        return group_name

    def _edge_as_3d_tuple_list(self, edge, vertices_3d):
        """
            Represents given edge object as list of control points
            suitable for draing in Maya
        """
        points = vertices_3d[edge['endpoints'], :]

        if 'curvature' in edge:
            control_coords = self._control_to_abs_coord(
                points[0, :2], points[1, :2], edge['curvature']
            )
            # to 3D
            control_coords = np.append(control_coords, 0)
            # Rearrange
            points = np.r_[
                [points[0]], [control_coords], [points[1]]
            ]

        return list(map(tuple, points))


if __name__ == "__main__":
    pattern = MayaPattern(
        'C:/Users/LENOVO/Desktop/Garment-Pattern-Estimation/data_generation/Patterns/skirt_per_panel.json'
    )
    pattern.load()
