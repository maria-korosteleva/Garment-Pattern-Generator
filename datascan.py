"""Emulate the result of scanning a garment on existing dataset of simulated garments"""

from __future__ import print_function
import os

# Maya
from maya import cmds
import maya.standalone 	

# My modules
import customconfig
# reload in case we are in Maya internal python environment
reload(customconfig)


# TODO do smth with repetitive code!
def init_mayapy():
    try: 
        print('Initilializing Maya tools...')
        maya.standalone.initialize()
        print('Load plugins')
        cmds.loadPlugin('mtoa.mll')  # https://stackoverflow.com/questions/50422566/how-to-register-arnold-render
        cmds.loadPlugin('objExport.mll')  # same as in https://forums.autodesk.com/t5/maya-programming/invalid-file-type-specified-atomimport/td-p/9121166
        
    except Exception as e: 
        print(e)
        print('Init failed')
        pass


def stop_mayapy():  
    maya.standalone.uninitialize() 
    print("Maya stopped")

# TODO repetive code with mayascene module
def load_body(bodyfilename):
    """Load body object to the scene"""
    body = cmds.file(bodyfilename, i=True, rnn=True)[0]
    body = cmds.rename(body, 'body#')

    # convert to cm heuristically
    # check for througth height (Y axis)
    # NOTE prone to fails if non-meter units are used for body
    bb = cmds.polyEvaluate(body, boundingBox=True)  # ((xmin,xmax), (ymin,ymax), (zmin,zmax))
    height = bb[1][1] - bb[1][0]
    if height < 3:  # meters
        cmds.scale(100, 100, 100, body, centerPivot=True, absolute=True)
        print('Warning: Body Mesh is found to use meters as units. Scaled up by 100 for cm')
    elif height < 10:  # decimeters
        cmds.scale(10, 10, 10, body, centerPivot=True, absolute=True)
        print('Warning: Body Mesh is found to use decimeters as units. Scaled up by 10 for cm')
    elif height > 250:  # millimiters or something strange
        cmds.scale(0.1, 0.1, 0.1, body, centerPivot=True, absolute=True)
        print('Warning: Body Mesh is found to use millimiters as units. Scaled down by 0.1 for cm')

    return body

if __name__ == "__main__":

    system_config = customconfig.Properties('system.json')  # Make sure it's in \Autodesk\MayaNNNN\
    path = system_config['templates_path']

    # ------ Dataset ------
    dataset = 'data_5_tee_200923-15-24-53'
    datapath = os.path.join(system_config['datasets_path'], dataset)
    data_props = customconfig.Properties(os.path.join(datapath, 'dataset_properties.json'))
    if not data_props['to_subfolders']:
        raise NotImplementedError('Scanning only works on datasets organized in subfolders')  # just for simplicity 

    # Body info -- in the dataset itself ?
    bodypath = os.path.join(system_config['bodies_path'], data_props['body'])

    # ------ Start Maya instance ------
    init_mayapy()
    import mayaqltools as mymaya  # has to import after maya is loaded
    reload(mymaya)  # reload in case we are in Maya internal python environment
    from mayaqltools import utils

    # ------ Main loop --------
    # load body to the scene
    body = load_body(bodypath)
    
    # go over the examples in the data
    to_ignore = ['renders']  # special dirs not to include in the pattern list
    root, dirs, files = next(os.walk(datapath))
    # cannot use os.scandir in python 2.7
    for name in dirs:
        if name not in to_ignore:
            dir_path = os.path.join(root, name)
            # load mesh
            garment_sim_file = os.path.join(dir_path, name + '_sim.obj')
            if not os.path.isfile(garment_sim_file):
                raise RuntimeError('Scan immitation::Missing file {} in the data directory {}'.format(garment_sim_file, dir_path))
            garment = cmds.file(garment_sim_file, i=True, rnn=True)[0]
            garment = cmds.rename(garment, name + '_sim#')
            
            # ---- scan ------ 
            mymaya.scan_imitation.remove_invisible(garment, [body])

            # save to original folder
            utils.save_mesh(garment, os.path.join(dir_path, name + '_scan_imitation.obj'))

            cmds.delete(garment)  # cleanup


    # End Maya instance
    stop_mayapy()  # ensures correct exit without errors