"""
    Module to batch-simulate garments from patterns in Maya.
    Note that Maya uses Python 2.7 (incl Maya 2020) hence this module is adapted to Python 2.7
"""
# Basic
from __future__ import print_function
import json
import os
import numpy as np
import time

# Maya
from maya import cmds
from maya import OpenMaya

# My module
import pattern.core as core
import qualothwrapper as qw
reload(core)
reload(qw)


class MayaGarment(core.BasicPattern):
    """
    Extends a pattern specification in custom JSON format to work with Maya
        Input:
            * Pattern template in custom JSON format
        * import panel to Maya scene TODO
        * cleaning imported stuff TODO
        * Basic operations on panels in Maya TODO
    """
    def __init__(self, pattern_file):
        super(MayaGarment, self).__init__(pattern_file)
        self.loaded_to_maya = False
        self.maya_shape = None
        self.maya_cloth_object = None
        self.last_verts = None
        self.current_verts = None
    
    def load(self, parent_group='experiment'):
        """
            Loads current pattern to Maya as curve collection.
            Groups them by panel and by pattern
        """
        # Load panels as curves
        maya_panel_names = []
        for panel_name in self.pattern['panels']:
            panel_maya = self._load_panel(panel_name)
            maya_panel_names.append(panel_maya)
        
        group_name = cmds.group(maya_panel_names, 
                                n=self.name,
                                p=parent_group)
        self.pattern['maya'] = group_name  # Maya modifies specified name for uniquness
        
        print("All panels loaded to Maya")

        # stitch them
        self._stitch_panels()

        self.loaded_to_maya = True

    def get_qlcloth_geomentry(self):
        """
            Find the first Qualoth cloth geometry object belonging to current pattern
        """
        if not self.maya_shape:
            children = cmds.listRelatives(self.pattern['maya'], ad=True)
            cloths = [obj for obj in children 
                      if 'qlCloth' in obj and 'Out' in obj and 'Shape' in obj]
            self.maya_shape = cloths[0]

        return self.maya_shape

    def get_qlcloth_props_obj(self):
        """
            Find the first qlCloth object belonging to current pattern
        """
        if not self.maya_cloth_object:
            children = cmds.listRelatives(self.pattern['maya'], ad=True)
            cloths = [obj for obj in children 
                      if 'qlCloth' in obj and 'Out' not in obj and 'Shape' in obj]
            self.maya_cloth_object = cloths[0]

        return self.maya_cloth_object

    def update_verts_info(self):
        """
            Retrieves current vertex positions from Maya & updates the last state.
            For best performance, should be called on each iteration of simulation
            Assumes the object is already loaded & stitched
        """
        # working with meshes http://www.fevrierdorian.com/blog/post/2011/09/27/Quickly-retrieve-vertex-positions-of-a-Maya-mesh-%28English-Translation%29
        cloth_dag = name_to_dag(self.get_qlcloth_geomentry())
        
        mesh = OpenMaya.MFnMesh(cloth_dag)
        maya_vertices = OpenMaya.MPointArray()
        mesh.getPoints(maya_vertices, OpenMaya.MSpace.kWorld)

        vertices = np.empty((maya_vertices.length(), 3))
        for i in range(maya_vertices.length()):
            for j in range(3):
                vertices[i, j] = maya_vertices[i][j]

        self.last_verts = self.current_verts
        self.current_verts = vertices

    def is_static(self, threshold):
        """
            Checks wether garment is in the static equilibrium
            Compares current state with the last recorded state
        """
        if self.last_verts is None:  # first iteration
            return False
        
        # Compare L1 norm per vertex
        # Checking vertices change is the same as checking if velocity is zero
        diff = np.abs(self.current_verts - self.last_verts)
        diff_L1 = np.sum(diff, axis=1)
        # DEBUG print(np.sum(diff), threshold * len(diff))
        if (diff_L1 < threshold).all():  # compare vertex-vize to be independent of #verts
            return True
        else:
            return False

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

    def _stitch_panels(self):
        """
            Create seams between qualoth panels.
            Assumes that panels are already loadeded (as curves).
            Assumes that after stitching every pattern becomes a single piece of geometry
            Returns
                Qulaoth cloth object name
        """

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


def name_to_dag(name):
    """returns a dag path given a name
        https://help.autodesk.com/view/MAYAUL/2016/ENU/?guid=__files_Maya_Python_API_Using_the_Maya_Python_API_htm
    """
    selectionList = OpenMaya.MSelectionList()
    selectionList.add(name)
    dagPath = OpenMaya.MDagPath()
    selectionList.getDagPath(0, dagPath)
    return dagPath


def save_mesh(garment, save_to):
    return 


def render(save_to):
    return


def record_fail(current_path, props):
    """records current simulation case as fail"""
    # discard last slash for basenme to work correctly
    if current_path[-1] == '/' or current_path[-1] == '\\':
        current_path = current_path[:-1] 
    
    name = os.path.basename(current_path)
    props['sim_fails'].append(name)


def init_sim(solver, props):
    """
        Basic simulation settings before starting simulation
    """
    cmds.setAttr(solver + '.selfCollision', 1)
    cmds.setAttr(solver + '.startTime', 1)
    cmds.setAttr(solver + '.solverStatistics', 0)  # for easy reading of console output
    cmds.playbackOptions(ps=0, max=props['max_sim_steps'])  # 0 playback speed = play every frame
    cmds.currentTime(1)  # needed to suppress "Frames skipped warning"


def run_sim(garment, body, experiment, save_to, props):
    """
        Setup and run simulation of the garment on the body
        Assumes garment is already properly aligned!
    """
    solver = qw.findSolver()

    # init
    init_sim(solver, props)

    # run -- Manual "play"
    # NOTE! It will run simulate all cloth existing in the scene
    start_time = time.time()
    for frame in range(1, props['max_sim_steps']):
        cmds.currentTime(frame)  # step
        garment.update_verts_info()
        if garment.is_static(props['static_threshold']):  # TODO Add penetration checks
            save_mesh(garment, save_to)
            render(save_to)
            break
    # Record time to sim + fps (or Sec per Frame =))
    # TODO make recording pattern-specific, not dataset-specific
    props['sim_time'] = (time.time() - start_time)
    props['spf'] = props['sim_time'] / frame
    props['fin_frame'] = frame

    # static equilibrium never detected -- might have false negs!
    if frame == props['max_sim_steps'] - 1:
        record_fail(save_to, props)
    

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
        sim_options = {
            'max_sim_steps': 1500, 
            'sim_fails': [], 
            'static_threshold': 0.01  # depends on the units used
        }

        qw.load_plugin()

        # --- future loop of batch processing ---
        experiment_name = start_experiment('test')

        garment = MayaGarment(
            'C:/Users/LENOVO/Desktop/Garment-Pattern-Estimation/data_generation/Patterns/skirt_maya_coords.json'
        )
        garment.load(experiment_name)
        garment.setMaterialProps()

        body_ref = load_body_as_collider(
            'F:/f_smpl_templatex300.obj', 
            garment.get_qlcloth_geomentry(),
            experiment_name
        )

        run_sim(garment, body_ref, 
                experiment_name, 
                'F:/GK-Pattern-Data-Gen/Sims', 
                sim_options)

        # Fin
        # clean_scene(experiment_name)
        print('Finished experiment', experiment_name)
        # TODO save to file
        print(sim_options)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
