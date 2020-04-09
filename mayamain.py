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
        self.loaded_to_maya = False
    
    def load(self, parent_group='experiment'):
        """
            Loads current pattern to Maya as curve collection.
            Groups them by panel and by pattern
        """
        maya_panel_names = []
        for panel_name in self.pattern['panels']:
            panel_maya = self._load_panel(panel_name)
            maya_panel_names.append(panel_maya)
        
        group_name = cmds.group(maya_panel_names, 
                                n=self.name,
                                p=parent_group)
        self.pattern['maya'] = group_name  # Maya modifies specified name for uniquness
        
        print("All panels loaded to Maya")
        self.loaded_to_maya = True

    def _load_panel(self, panel_name):
        """
            Loads curves contituting given panel to Maya. 
            Goups them per panel
        """
        panel = self.pattern['panels'][panel_name]
        vertices = np.asarray(panel['vertices'])

        # now draw edges
        curve_names = []
        for edge in panel['edges']:
            curve_points = self._edge_as_3d_tuple_list(
                edge, vertices, panel['translation']
            )
            curve = cmds.curve(p=curve_points, d=(len(curve_points) - 1))
            curve_names.append(curve)
            edge['maya'] = curve
        # Group edges        
        curve_group = cmds.group(curve_names, n='curves')
        panel['maya_curves'] = curve_group  # Maya modifies specified name for uniquness

        # Create geometry
        panel_geom = qw.qlCreatePattern(curve_group)

        # take out the solver node -- created only once per scene, no need to store
        solvers = [obj for obj in panel_geom if 'Solver' in obj]
        if solvers:
            panel_geom = list(set(panel_geom) - set(solvers))

        panel['qualoth'] = panel_geom  # note that the list might get invalid 
                                       # after stitching -- use carefully

        # group all objects belonging to a panel
        panel_group = cmds.group(panel_geom + [curve_group], n=panel_name)
        panel['maya_group'] = panel_group

        return panel_group

    def _edge_as_3d_tuple_list(self, edge, vertices, translation_3d):
        """
            Represents given edge object as list of control points
            suitable for draing in Maya
        """
        points = vertices[edge['endpoints'], :]
        if 'curvature' in edge:
            control_coords = self._control_to_abs_coord(
                points[0], points[1], edge['curvature']
            )
            # Rearrange
            points = np.r_[
                [points[0]], [control_coords], [points[1]]
            ]
        # to 3D
        points = np.c_[points, np.zeros(len(points))]

        # 3D placement
        points += translation_3d

        return list(map(tuple, points))

    def stitch_panels(self):
        """
            Create seams between qualoth panels.
            Calls to load panels if they are not already loaded.
            Assumes that after stitching the pattern becomes a single piece of geometry
            Returns
                Qulaoth cloth object name
        """
        if not self.loaded_to_maya:
            self.load('stitching')

        stitches = []
        for stitch in self.pattern['stitches']:
            from_curve = self._maya_curve_name(stitch['from'])
            # TODO add support for multiple "to" components
            to_curve = self._maya_curve_name(stitch['to'])
            stitch_id = qw.qlCreateSeam(from_curve, to_curve)
            stitch['maya'] = stitch_id
            stitches.append(stitch_id)

        cmds.parent(stitches, self.pattern['maya'])

        return self._find_qlcloth_object()

    def _maya_curve_name(self, address):
        """ Shortcut to retrieve the name of curve corresponding to the edge"""
        panel_name = address['panel']
        edge_id = address['edge']
        return self.pattern['panels'][panel_name]['edges'][edge_id]['maya']

    def _find_qlcloth_object(self):
        """
            Find the first Qualoth cloth object belonging to current pattern
        """
        children = cmds.listRelatives(self.pattern['maya'], ad=True)
        cloths = [obj for obj in children 
                  if 'qlCloth' in obj and 'Out' in obj and 'Shape' not in obj]

        return cloths[0]


def load_body(filename, group_name):
    body = cmds.file(filename, i=True, rnn=True)
    cmds.parent(body[0], group_name)
    return body[0]


def run_sim(garment, body):
    """
        Setup and run simulation of the garment on the body
        Assumes garment is already properly aligned!
    """
    # Setup anti-collisions
    print(garment, body)
    qw.qlCreateCollider(garment, body)
    # TODO activate self-collision


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

    try:
        experiment_name = start_experiment('test')
        qw.load_plugin()

        pattern = MayaPattern(
            'C:/Users/LENOVO/Desktop/Garment-Pattern-Estimation/data_generation/Patterns/skirt_maya_coords.json'
        )
        pattern.load(experiment_name)
        cloth_ref = pattern.stitch_panels()

        body_ref = load_body('F:/f_smpl_templatex300.obj', experiment_name)

        run_sim(cloth_ref, body_ref)

        # Fin
        # clean_scene(experiment_name)
        print('Finished experiment', experiment_name)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
