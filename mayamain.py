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

# Arnold
import mtoa.utils as mutils

# My modules
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
        self.maya_shape = None
        self.maya_cloth_object = None
        self.maya_shape_dag = None
        self.last_verts = None
        self.current_verts = None
    
    def load(self, parent_group=None):
        """
            Loads current pattern to Maya as curve collection.
            Groups them by panel and by pattern
        """
        # Load panels as curves
        maya_panel_names = []
        for panel_name in self.pattern['panels']:
            panel_maya = self._load_panel(panel_name)
            maya_panel_names.append(panel_maya)
        
        group_name = cmds.group(maya_panel_names, n=self.name)
        if parent_group is not None:
            group_name = cmds.parent(group_name, parent_group)

        self.pattern['maya'] = group_name
        
        # assemble
        self._stitch_panels()

        print('Garment ' + self.name + 'is loaded to Maya')

    def setMaterialProps(self, shader=None):
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

        if shader is not None:
            cmds.select(self.get_qlcloth_geomentry())
            cmds.hyperShade(assign=shader)

    def add_colliders(self, *obstacles):
        """
            Adds given Maya objects as colliders of the garment
        """
        for obj in obstacles:
            collider = qw.qlCreateCollider(
                self.get_qlcloth_geomentry(), 
                obj
            )
            # properties
            # TODO experiment with the value -- it's now set arbitrarily
            qw.setColliderFriction(collider, 0.5)
            # organize object tree
            cmds.parent(collider, self.pattern['maya'])

    def clean(self, delete=False):
        """ Hides/removes the garment from Maya scene 
            NOTE all of the maya ids assosiated with the garment become invalidated, 
            if delete flag is True
        """
        cmds.hide(self.pattern['maya'])
        if delete:
            cmds.delete(self.pattern['maya'])

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

    def get_qlcloth_geom_dag(self):
        """
            returns DAG reference to cloth shape object
        """
        if not self.maya_shape_dag:
            # https://help.autodesk.com/view/MAYAUL/2016/ENU/?guid=__files_Maya_Python_API_Using_the_Maya_Python_API_htm
            selectionList = OpenMaya.MSelectionList()
            selectionList.add(self.get_qlcloth_geomentry())
            self.maya_shape_dag = OpenMaya.MDagPath()
            selectionList.getDagPath(0, self.maya_shape_dag)

        return self.maya_shape_dag

    def update_verts_info(self):
        """
            Retrieves current vertex positions from Maya & updates the last state.
            For best performance, should be called on each iteration of simulation
            Assumes the object is already loaded & stitched
        """
        # working with meshes http://www.fevrierdorian.com/blog/post/2011/09/27/Quickly-retrieve-vertex-positions-of-a-Maya-mesh-%28English-Translation%29
        cloth_dag = self.get_qlcloth_geom_dag()
        
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

    def save_mesh(self, folder=''):
        """
            Saves cloth as obj file to a given folder or 
            to the folder with the pattern if not given
        """
        if self.current_verts is None:
            raise ValueError('MayaGarment::Pattern is not yet loaded')

        if folder:
            filepath = folder
        else:
            filepath = self.path
        filepath = os.path.join(filepath, self.name + '_sim.obj')

        cmds.select(self.get_qlcloth_geomentry())
        cmds.file(
            filepath + '.obj',  # Maya 2020 stupidly cuts file extention 
            typ='OBJExport',
            es=1,  # export selected
            op='groups=0;ptgroups=0;materials=0;smoothing=0;normals=1'  # very simple
        )

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

    def _maya_curve_name(self, address):
        """ Shortcut to retrieve the name of curve corresponding to the edge"""
        panel_name = address['panel']
        edge_id = address['edge']
        return self.pattern['panels'][panel_name]['edges'][edge_id]['maya']


class Scene(object):
    """
        Decribes scene setup
        Assumes 
            * body the scene revolved aroung faces z+ direction
    """
    def __init__(self, body_obj, options):
        """
            Set up scene for rendering using loaded body as a reference
        """
        # load body to be used as a translation reference
        self.body_filepath = body_obj
        self.body = cmds.file(body_obj, i=True, rnn=True)[0]
        self.body = cmds.rename(self.body, 'body#')

        # Add 'floor'
        self.floor = self._add_floor(self.body)[0]

        # Put camera. NOTE Assumes body is facing +z direction
        self.camera = cmds.camera()
        cmds.viewFit(self.camera, self.body, f=0.75)

        # Add light (Arnold)
        self.light = mutils.createLocator('aiSkyDomeLight', asLight=True)

        # create materials
        self.body_shader = self._new_lambert(options['body_color'], self.body)
        self.floor_shader = self._new_lambert(options['floor_color'], self.floor)
        self.cloth_shader = self._new_lambert(options['cloth_color'])

    def render(self, save_to):
        """
            Makes a rendering of a current scene, and saves it to a given path
        """
        return

    def _add_floor(self, target):
        """
            adds a floor under a given object
        """
        target_bb = cmds.exactWorldBoundingBox(target)

        size = 10 * (target_bb[4] - target_bb[1])
        floor = cmds.polyPlane(n='floor', w=size, h=size)

        # place under the body
        floor_level = target_bb[1]
        cmds.move((target_bb[3] + target_bb[0]) / 2,  # bbox center
                  floor_level, 
                  (target_bb[5] + target_bb[2]) / 2,  # bbox center
                  floor, a=1)

        return floor

    def _new_lambert(self, color, target=None):
        """created a new shader node with given color"""
        shader = cmds.shadingNode('lambert', asShader=True)
        cmds.setAttr((shader + '.color'), 
                     color[0], color[1], color[2],
                     type='double3')

        if target is not None:
            cmds.select(target)
            cmds.hyperShade(assign=shader)

        return shader
        

def init_sim(solver, props):
    """
        Basic simulation settings before starting simulation
    """
    cmds.setAttr(solver + '.selfCollision', 1)
    cmds.setAttr(solver + '.startTime', 1)
    cmds.setAttr(solver + '.solverStatistics', 0)  # for easy reading of console output
    cmds.playbackOptions(ps=0, max=props['max_sim_steps'])  # 0 playback speed = play every frame


def run_sim(garment, props):
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
    # sim without checks
    for frame in range(1, props['min_sim_steps']):
        cmds.currentTime(frame)  # step

    # sim with checks
    for frame in range(props['min_sim_steps'], props['max_sim_steps']):
        cmds.currentTime(frame)  # step
        garment.update_verts_info()
        if garment.is_static(props['static_threshold']):  # TODO Add penetration checks
            # Success!
            break
    # Record time to sim + fps (or Sec per Frame =))
    # TODO make recording pattern-specific, not dataset-specific
    props['sim_time'] = (time.time() - start_time)
    props['spf'] = props['sim_time'] / frame
    props['fin_frame'] = frame

    # Fail check: static equilibrium never detected -- might have false negs!
    # TODO should I save the result anyway? 
    if frame == props['max_sim_steps'] - 1:
        props['sim_fails'].append(garment.name)


# ----------- Main loop --------------
def main():
    try:
        # ----- Init -----
        options = {
            'sim': {
                'max_sim_steps': 20, 
                'min_sim_steps': 10,  # no need to check for static equilibrium until min_steps 
                'sim_fails': [], 
                'static_threshold': 0.05  # 0.01  # depends on the units used
            },
            'render': {
                'body_color': [0.1, 0.2, 0.7], 
                'cloth_color': [0.8, 0.2, 0.2],
                'floor_color': [0.1, 0.1, 0.1]
            }
            
        }
        qw.load_plugin()

        scene = Scene('F:/f_smpl_templatex300.obj', options['render'])

        # --- future loop of batch processing ---
        garment = MayaGarment(
            'C:/Users/LENOVO/Desktop/Garment-Pattern-Estimation/data_generation/Patterns/skirt_maya_coords.json'
        )
        garment.load()
        garment.setMaterialProps(scene.cloth_shader)
        garment.add_colliders(scene.body, scene.floor)

        run_sim(garment, 
                options['sim'])

        garment.save_mesh('F:/GK-Pattern-Data-Gen/Sims')
        render('F:/GK-Pattern-Data-Gen/Sims')

        # Fin
        garment.clean()
        print('Finished experiment')
        # TODO save to file
        print(options)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
