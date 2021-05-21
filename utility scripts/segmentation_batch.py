"""
    Recover segmentation for alredy simulated garments
    
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

    # ------ Datasets ------
    dataset_folders = [
        'updates_tests_skirt_4_panels_random'
    ]
    print_skipped_files = False
    skipped_files = dict.fromkeys(dataset_folders)
    for key in skipped_files:
        skipped_files[key] = {}

    # ------ Start Maya instance ------
    init_mayapy()
    import mayaqltools as mymaya  # has to import after maya is loaded
    reload(mymaya)  # reload in case we are in Maya internal python environment
    from mayaqltools import qualothwrapper as qw

    qw.load_plugin()

    for dataset in dataset_folders:
        datapath = os.path.join(system_config['datasets_path'], dataset)
        # print(datapath)
        dataset_file = os.path.join(datapath, 'dataset_properties.json')
        data_props = customconfig.Properties(dataset_file)
        if not data_props['to_subfolders']:
            raise NotImplementedError('Only works on datasets organized in subfolders')  # just for simplicity 

        # ------ Main loop --------        
        # go over the examples in the data
        start_time = time.time()
        to_ignore = ['renders']  # special dirs not to include in the pattern list
        root, dirs, files = next(os.walk(datapath))  # cannot use os.scandir in python 2.7

        for name in dirs:
            if name not in to_ignore:
                dir_path = os.path.join(root, name)

                # print(name)

                _, elem_dirs, elem_files = next(os.walk(dir_path))
                
                if not any([name + '_sim.obj' in filename for filename in elem_files]):
                    # simulation result does not exist
                    print('Warning::Skipped {} as .obj file does not exist'.format(name))
                    continue

                if any(['sim_segmentation' in filename for filename in elem_files]):
                    # already processed -- continue
                    continue
                
                # load pattern in Maya
                garment = mymaya.MayaGarment(os.path.join(dir_path, 'specification.json'))
                garment.load(config=data_props['sim']['config'])

                # check that the operation can be applied safely
                num_vert_loaded = len(garment.current_verts)
                sim_mesh = mymaya.utils.load_file(os.path.join(dir_path, name + '_sim.obj'))
                num_verts_original = cmds.polyEvaluate(vertex=True)

                if num_vert_loaded != num_verts_original:
                    # cannot re-apply the segmentation because counts are wrong
                    skipped_files[dataset][name] = '{}: {}'.format(num_verts_original, num_vert_loaded)
                    continue
                
                # save segmentation to original folder
                filepath = os.path.join(dir_path, name + '_sim_segmentation.txt')
                with open(filepath, 'w') as f:
                    for panel_name in garment.vertex_labels:
                        f.write("%s\n" % panel_name)

                garment.clean(True)  # cleanup

        # update props & save
        passed = time.time() - start_time
        passed = timedelta(seconds=passed)

        print('Mesh segmentation on {} performed successfully for {}!!!'.format(dataset, str(passed)))


    # print skipped files if any
    print('\nFiles skipped:')
    for dataset in skipped_files:
        if len(skipped_files[dataset]) > 0:
            print('{}:{} datapoints skipped'.format(dataset, len(skipped_files[dataset])))
            if print_skipped_files:
                for name, counts in skipped_files[dataset].items():
                    print('{} -- {}'.format(name, counts))
            print('->')

    # End Maya instance
    stop_mayapy()  # ensures correct exit without errors