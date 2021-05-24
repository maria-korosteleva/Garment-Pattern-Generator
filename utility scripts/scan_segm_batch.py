"""
    transfer segmentation labels from sim to scan data
    
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


def transfer_segm_labels(verts_before, mesh, dir_path, name):
    """
        Save segmentation labels for mesh after scan imitation
    """
    verts_after = utils.get_vertices_np(mesh)
    verts_mapping = utils.match_vert_lists(verts_after, verts_before)

    # print(os.path.join(dir_path, name + '_sim_segmentation.txt'))

    with open(os.path.join(dir_path, name + '_sim_segmentation.txt'), 'r') as f:
        vert_labels = [line.rstrip() for line in f]  # remove \n
    scan_labels = [vert_labels[i] for i in verts_mapping]

    filepath = os.path.join(dir_path, name + '_scan_imitation_segmentation.txt')
    with open(filepath, 'w') as f:
        for panel_name in scan_labels:
            f.write("%s\n" % panel_name)


if __name__ == "__main__":

    system_config = customconfig.Properties('system.json')  # Make sure it's in \Autodesk\MayaNNNN\
    path = system_config['templates_path']

    # ------ Datasets ------
    dataset_folders = [
        # 'test_150_dress_210401-17-57-12',
        # 'test_150_jacket_hood_sleeveless_210331-11-16-33',
        # 'test_150_jacket_sleeveless_210331-15-54-26',
        # 'test_150_jumpsuit_210401-16-28-21',
        'test_150_skirt_waistband_210331-16-05-37',
        # 'test_150_tee_hood_210401-15-25-29',
        # 'test_150_wb_jumpsuit_sleeveless_210404-11-27-30'
    ]

    # ------ Start Maya instance ------
    init_mayapy()
    import mayaqltools as mymaya  # has to import after maya is loaded
    reload(mymaya)  # reload in case we are in Maya internal python environment
    from mayaqltools import utils

    skipped_datapoints = dict.fromkeys(dataset_folders)
    for key in skipped_datapoints:  
        skipped_datapoints[key] = {}

    for dataset in dataset_folders:
        datapath = os.path.join(system_config['datasets_path'], 'test', dataset)
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

        for name in dirs:
            if name not in to_ignore:
                dir_path = os.path.join(root, name)

                # skip if already has a corresponding file
                _, elem_dirs, elem_files = next(os.walk(dir_path))

                if any(['scan_imitation_segmentation.txt' in filename for filename in elem_files]):
                    print('Datascan::Warninig::Skipped {} as already processed'.format(name))
                    continue

                if not any(['scan_imitation.obj' in filename for filename in elem_files]):
                    skipped_datapoints[dataset][name] = 'Datascan::Warninig::Skipped {} as the scan imitation obj is missing'.format(name)
                    print(skipped_datapoints[dataset][name])
                    continue
                
                if not any([name + '_sim.obj' in filename for filename in elem_files]):
                    # simulation result does not exist
                    skipped_datapoints[dataset][name] = 'Datascan::Warning::Skipped {} as .obj file does not exist'.format(name)
                    print(skipped_datapoints[dataset][name])
                    continue
                
                if not any([name + '_sim_segmentation.txt' in filename for filename in elem_files]):
                    # segmentation labels file for sim does not exist
                    skipped_datapoints[dataset][name] = 'Datascan::Warning::{}:: Skipped segmentation transfer as segmentation file does not exist'.format(name)
                    print(skipped_datapoints[dataset][name])
                    continue

                # load mesh
                garment_sim = utils.load_file(os.path.join(dir_path, name + '_sim.obj'), name + '_sim')
                mesh_sim, _ = utils.get_mesh_dag(garment_sim)
                verts_before = utils.get_vertices_np(mesh_sim)

                garment_scan = utils.load_file(os.path.join(dir_path, name + '_scan_imitation.obj'), name + '_scan')
                mesh_scan, _ = utils.get_mesh_dag(garment_scan)

                # transfer the segmentation labels 
                try:
                    transfer_segm_labels(verts_before, mesh_scan, dir_path, name)
                except (IndexError, ValueError) as e:
                    print(e)
                    skipped_datapoints[dataset][name] = str(e)
            
                cmds.delete(garment_sim)  # cleanup
                cmds.delete(garment_scan)  # cleanup

        # update props & save
        passed = time.time() - start_time
        print('Processes dataset {} for {}'.format(dataset, str(timedelta(seconds=passed))))

    print('\nDatapoints skipped:')
    for dataset in skipped_datapoints:
        if len(skipped_datapoints[dataset]) > 0:
            print('{}:{} datapoints skipped'.format(dataset, len(skipped_datapoints[dataset])))
            print('->')

    # End Maya instance
    stop_mayapy()  # ensures correct exit without errors