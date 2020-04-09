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
import pattern.core as core
reload(core)
import qualothwrapper as qw
reload(qw)


class MayaPattern(core.BasicPattern):
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
    
    def load(self, parent_group='experiment'):
        """
            Loads current pattern to Maya as curve collection.
            Groups them by panel and by pattern
        """
        maya_panel_names = []
        for panel_name in self.pattern['panels']:
            panel_maya = self._load_panel(panel_name)
            maya_panel_names.append(panel_maya)
        
        print(maya_panel_names)
        group_name = cmds.group(maya_panel_names, 
                                n=self.name,
                                p=parent_group)
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

        # now draw edges
        curve_names = []
        for edge in panel['edges']:
            curve_points = self._edge_as_3d_tuple_list(edge, vertices)            
            curve = cmds.curve(p=curve_points, d=(len(curve_points) - 1))
            curve_names.append(curve)
            edge['maya'] = curve
        # Group edges        
        curve_group = cmds.group(curve_names, n='curves')
        panel['maya_curves'] = curve_group  # Maya modifies specified name for uniquness

        # Create geometry
        panel_geom = qw.qlCreatePattern(curve_group)

        # take out the solver node -- created with the first panel
        solvers = [obj for obj in panel_geom if 'Solver' in obj]
        if solvers:
            self.pattern['qlSover'] = solvers
            panel_geom = list(set(panel_geom) - set(solvers))

        panel['qualoth'] = panel_geom

        # group all objects belonging to a panel
        panel_group = cmds.group(panel_geom + [curve_group], n=panel_name)
        panel['maya_group'] = panel_group

        return panel_group

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


def load_body(filename, group_name):
    body = cmds.file(filename, i=True, rnn=True)
    cmds.parent(body[0], group_name)


def start_experiment(nametag):
    cmds.namespace(set=':')  # switch to default namespace JIC

    # group all objects under a common node
    experiment_name = cmds.group(em=True, n=nametag)

    # activate new namespace to prevet nameclash
    namespace = cmds.namespace(add=experiment_name)
    cmds.namespace(set=namespace)
    print('Starting experiment', experiment_name)
    return experiment_name


def clean_scene(top_group, delete=False):
    cmds.hide(top_group)
    if delete:
        cmds.delete(top_group)
    # return from custom namespaces, if any
    cmds.namespace(set=':')
    return


# ----------- Main loop --------------
def main():
    experiment_name = start_experiment('test')
    qw.load_plugin()

    pattern = MayaPattern(
        'C:/Users/LENOVO/Desktop/Garment-Pattern-Estimation/data_generation/Patterns/skirt_per_panel.json'
    )
    pattern.load(experiment_name)

    body_ref = load_body('F:/f_smpl_template.obj', experiment_name)

    # Fin
    clean_scene(experiment_name)
    print('Finished experiment', experiment_name)


if __name__ == "__main__":
    main()
