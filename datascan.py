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


# Had to make copy of functions from datasim.py, becuase of issues with importing maya-related packages
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


if __name__ == "__main__":

    system_config = customconfig.Properties('system.json')  # Make sure it's in \Autodesk\MayaNNNN\
    path = system_config['templates_path']

    # ------ Dataset ------
    dataset = 'data_5_tee_200923-15-24-53'
    datapath = os.path.join(system_config['datasets_path'], dataset)
    data_props = customconfig.Properties(os.path.join(datapath, 'dataset_properties.json'))
    if not data_props['to_subfolders']:
        raise NotImplementedError('Scanning only works on datasets organized in subfolders')  # just for simplicity 

    # ------ Start Maya instance ------
    init_mayapy()
    import mayaqltools as mymaya  # has to import after maya is loaded
    reload(mymaya)  # reload in case we are in Maya internal python environment
    from mayaqltools import utils

    # ------ Main loop --------
    # load body to the scene
    body = utils.load_file(os.path.join(system_config['bodies_path'], data_props['body']), 'body')
    utils.scale_to_cm(body)
    
    # go over the examples in the data
    to_ignore = ['renders']  # special dirs not to include in the pattern list
    root, dirs, files = next(os.walk(datapath))
    # cannot use os.scandir in python 2.7
    for name in dirs:
        if name not in to_ignore:
            dir_path = os.path.join(root, name)
            # load mesh
            garment = utils.load_file(os.path.join(dir_path, name + '_sim.obj'), name + '_sim')
            
            # do what we are here for
            mymaya.scan_imitation.remove_invisible(garment, [body])

            # save to original folder
            utils.save_mesh(garment, os.path.join(dir_path, name + '_scan_imitation.obj'))
            
            cmds.delete(garment)  # cleanup


    # End Maya instance
    stop_mayapy()  # ensures correct exit without errors