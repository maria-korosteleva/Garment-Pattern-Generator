"""
    Qualoth scripts are written in MEL. 
    This module makes a python interface to them
    Notes:
        * this module is Python 2.7-friendly
        * Error checks are sparse to save coding time & lines. 
            This sould not be a problem during the normal workflow
    
"""
from __future__ import print_function
import time

from maya import mel
from maya import cmds


def load_plugin():
    """
        Forces loading Qualoth plugin into Maya. 
        Note that plugin should be installed and licensed to use it!
        Inquire here: http://www.fxgear.net/vfxpricing
    """
    maya_year = int(mel.eval('getApplicationVersionAsFloat'))
    plugin_name = 'qualoth_' + str(maya_year) + '_x64'
    print('Loading ', plugin_name)

    cmds.loadPlugin(plugin_name)


# -------- Wrappers -----------
# Make sure that Qualoth plugin is loaded before running any wrappers!

def qlCreatePattern(curves_group):
    """
        Converts given 2D closed curve to a flat geometry piece
    """
    objects_before = cmds.ls(assemblies=True)
    # run
    cmds.select(curves_group)
    mel.eval('qlCreatePattern()')
    
    # Identify newly created objects
    objects_after = cmds.ls(assemblies=True)
    # No need for symmetric difference because we don't care if some objects were deleted
    return list(set(objects_after) - set(objects_before))


def qlCreateSeam(curve1, curve2):
    """
        Create a seam between two selected curves
        TODO add support for 1-many stitches
    """
    cmds.select([curve1, curve2])
    # Operates on selection
    seam_shape = mel.eval('qlCreateSeam()')
    return seam_shape


def qlCreateCollider(cloth, target):
    """
        Marks object as a collider object for cloth --
        eshures that cloth won't penetrate body when simulated
    """
    objects_before = cmds.ls(assemblies=True)

    cmds.select([cloth, target])
    # Operates on selection
    mel.eval('qlCreateCollider()')

    objects_after = cmds.ls(assemblies=True)
    return list(set(objects_after) - set(objects_before))


# ------- Higher-level functions --------

def _init_sim(solver, config):
    """
        Basic simulation settings before starting simulation
    """
    cmds.setAttr(solver + '.selfCollision', 1)
    cmds.setAttr(solver + '.startTime', 1)
    cmds.setAttr(solver + '.solverStatistics', 0)  # for easy reading of console output
    cmds.playbackOptions(ps=0, max=config['max_sim_steps'])  # 0 playback speed = play every frame


def run_sim(garment, props):
    """
        Setup and run cloth simulator untill static equlibrium of 
        a garment is achieved.
        Note:
            * Assumes garment is already properly aligned!
            * All of the garments existing in Maya scene will be simulated
                because solver is shared!!
    """
    solver = findSolver()
    config = props['config']
    _init_sim(solver, config)

    start_time = time.time()
    # skip checks for first few frames
    for frame in range(1, config['min_sim_steps']):
        cmds.currentTime(frame)  # step
        garment.cache_if_enabled(frame)

    for frame in range(config['min_sim_steps'], config['max_sim_steps']):
        cmds.currentTime(frame)  # step
        garment.cache_if_enabled(frame)
        garment.update_verts_info()
        if garment.is_static(config['static_threshold']):  
            # TODO Add penetration checks
            # Success!
            break

    # Fail check: static equilibrium never detected -- might have false negs!
    if frame == config['max_sim_steps'] - 1:
        props['stats']['sim_fails'].append(garment.name)

    # TODO make recording pattern-specific, not dataset-specific
    props['stats']['sim_time'].append(time.time() - start_time)
    props['stats']['spf'].append(props['stats']['sim_time'][-1] / frame)
    props['stats']['fin_frame'].append(frame)


def findSolver():
    """
        Returns the name of the qlSover existing in the scene
        (usully solver is created once per scene)
    """
    solver = cmds.ls('*qlSolver*Shape*')
    return solver[0]


def setColliderFriction(collider_objects, friction_value):
    """Sets the level of friction of the given collider to friction_value"""

    main_collider = [obj for obj in collider_objects if 'Offset' not in obj]
    collider_shape = cmds.listRelatives(main_collider[0], shapes=True)

    cmds.setAttr(collider_shape[0] + '.friction', friction_value)
