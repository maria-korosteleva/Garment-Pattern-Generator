"""
    Emulate the result of scanning a garment on existing dataset of simulated garments
    
    IMPORTANT!! This script need to be run with mayapy to get access to Autodesk Maya Python API. 
        E.g., on Windows the command could look like this: 
        d:/Autodesk/Maya2020/bin/mayapy.exe "./data_generation/datascan.py"
    """

from __future__ import print_function
import os
import time
from datetime import timedelta

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

    # print(system_config['datasets_path'])

    # ------ Datasets ------
    dataset_folders = [
        'updates_tests_1000_skirt_4_panels'
    ]

    # ------ Start Maya instance ------
    init_mayapy()
    import mayaqltools as mymaya  # has to import after maya is loaded
    reload(mymaya)  # reload in case we are in Maya internal python environment
    from mayaqltools import utils

    for dataset in dataset_folders:
        datapath = os.path.join(system_config['datasets_path'], dataset)
        # print(datapath)
        dataset_file = os.path.join(datapath, 'dataset_properties.json')
        data_props = customconfig.Properties(dataset_file)
        if not data_props['to_subfolders']:
            raise NotImplementedError('Scanning only works on datasets organized in subfolders')  # just for simplicity 

        # ------ Main loop --------
        # go over the examples in the data
        start_time = time.time()
        to_ignore = ['renders']  # special dirs not to include in the pattern list
        root, dirs, files = next(os.walk(datapath))  # cannot use os.scandir in python 2.7

        verts_removed = {'sim': [], 'scan_imitation': []}
        for name in dirs:
            if name not in to_ignore:
                dir_path = os.path.join(root, name)
                
                for tag in ['sim', 'scan_imitation']:
                    obj_name = name + '_' + tag + '.obj'

                    # check exists  
                    _, elem_dirs, elem_files = next(os.walk(dir_path))
                    if not any([obj_name in filename for filename in elem_files]):
                        # simulation result does not exist
                        print('Meshes Cleanup::Warning::Skipped {} as .obj file does not exist'.format(obj_name))
                        continue
                    
                    # load mesh
                    garment = utils.load_file(os.path.join(dir_path, obj_name), name)
                    
                    num_verts_before = cmds.polyEvaluate(garment, vertex=True)

                    # clean
                    cmds.polyClean(garment)

                    num_verts_after = cmds.polyEvaluate(garment, vertex=True)

                    verts_removed[tag].append(num_verts_after - num_verts_before)

                    print('{}: {} removed'.format(obj_name, num_verts_after - num_verts_before))

                    # save to original folder (overrides original file)
                    utils.save_mesh(garment, os.path.join(dir_path, obj_name))
                
                    cmds.delete(garment)  # cleanup

        # update props & save
        passed = time.time() - start_time
        passed = timedelta(seconds=passed)

        print('Mesh cleanup on {} performed successfully for {}!!!'.format(dataset, str(passed)))
        print('From sims: {}. From scans: {}.'.format(
            sum(verts_removed['sim']) / len(verts_removed['sim']),
            sum(verts_removed['scan_imitation']) / len(verts_removed['scan_imitation'])
        ))

    # End Maya instance
    stop_mayapy()  # ensures correct exit without errors