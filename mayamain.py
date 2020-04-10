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
import qualothwrapper as qw
reload(core)
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

        # note that the list might get invalid after stitching
        panel['qualoth'] = panel_geom  

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

        for stitch in self.pattern['stitches']:
            from_curve = self._maya_curve_name(stitch['from'])
            # TODO add support for multiple "to" components
            to_curve = self._maya_curve_name(stitch['to'])
            stitch_id = qw.qlCreateSeam(from_curve, to_curve)
            stitch_id = cmds.parent(stitch_id, self.pattern['maya'])  # organization
            stitch['maya'] = stitch_id[0]

    def setMaterialProps(self):
        """
            Sets material properties for the cloth object created from current panel
        """
        # TODO accept input from file
        # TODO Make a standalone function? 
        cloth = self.get_qlcloth_props_obj()

        # Controls stretchness of the fabric
        cmds.setAttr(cloth + '.stretch', 100)

        # Friction between cloth and itself 
        # (friction with body controlled by collider props)
        cmds.setAttr(cloth + '.friction', 0.25)

    def _maya_curve_name(self, address):
        """ Shortcut to retrieve the name of curve corresponding to the edge"""
        panel_name = address['panel']
        edge_id = address['edge']
        return self.pattern['panels'][panel_name]['edges'][edge_id]['maya']

    def get_qlcloth_geomentry(self):
        """
            Find the first Qualoth cloth geometry object belonging to current pattern
        """
        children = cmds.listRelatives(self.pattern['maya'], ad=True)
        cloths = [obj for obj in children 
                  if 'qlCloth' in obj and 'Out' in obj and 'Shape' in obj]

        return cloths[0]

    def get_qlcloth_props_obj(self):
        """
            Find the first qlCloth object belonging to current pattern
        """
        children = cmds.listRelatives(self.pattern['maya'], ad=True)
        cloths = [obj for obj in children 
                  if 'qlCloth' in obj and 'Out' not in obj and 'Shape' in obj]

        return cloths[0]


def load_body_as_collider(filename, garment, experiment):
    solver = qw.findSolver()

    body = cmds.file(filename, i=True, rnn=True)
    body = cmds.parent(body[0], experiment)

    # Setup collision handling
    collider_objects = qw.qlCreateCollider(garment, body[0])
    collider_objects = cmds.parent(collider_objects, experiment)

    # add body properties
    # TODO experiment with the value -- it's now set randomly
    qw.setColliderFriction(collider_objects, 0.5)

    return body[0]


def run_sim(garment, body, experiment, save_to):
    """
        Setup and run simulation of the garment on the body
        Assumes garment is already properly aligned!
    """
    solver = qw.findSolver()

    # properties
    cmds.setAttr(solver + '.selfCollision', 1)
    cmds.setAttr(solver + '.startTime', 1)
    cmds.setAttr(
        solver + '.postSimScript', 
        'print "testPostSim";',  
        type='string' 
    )

    # run
    # NOTE! It will run simulate all cloth existing in the scene
    cmds.playbackOptions(ps=0)  # 0 playback speed = play every frame
    cmds.currentTime(1)  # needed to suppress "Frames skipped warning"

    # Manual "play"
    for frame in range(1, 100):
        cmds.currentTime(frame)
        # TODO Check if it's ok to finish simulation
    
    # TODO record time to sim + fps (or Sec per Frame =))


def start_experiment(nametag):
    cmds.namespace(set=':')  # switch to default namespace JIC

    # group all objects under a common node
    experiment_name = cmds.group(em=True, n=nametag)
    
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
        pattern.stitch_panels()
        pattern.setMaterialProps()
        cloth_ref = pattern.get_qlcloth_geomentry()

        body_ref = load_body_as_collider(
            'F:/f_smpl_templatex300.obj', 
            cloth_ref,
            experiment_name
        )

        run_sim(cloth_ref, body_ref, experiment_name, 'F:/GK-Pattern-Data-Gen/Sims/')

        # Fin
        # clean_scene(experiment_name)
        print('Finished experiment', experiment_name)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
