"""
    Emulate the result of scanning a garment on existing dataset of simulated garments

    Support resuming functionality by default -- if you run on the dataset that already has some of the outputs, the datapoints will be skipped rather then re-evaluated
    
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
    path = system_config['templates_path']

    # ------ Datasets ------
    dataset_folders = [
        'data_5000_tee_200924-16-57-59_regen_210327-15-20-23',
        'data_5000_skirt_4_panels_201019-12-23-24_regen_210331-16-18-32'
    ]

    # ------ Start Maya instance ------
    init_mayapy()
    import mayaqltools as mymaya  # has to import after maya is loaded
    reload(mymaya)  # reload in case we are in Maya internal python environment
    from mayaqltools import utils

    for dataset in dataset_folders:
        datapath = os.path.join(system_config['datasets_path'], dataset)
        print(datapath)
        dataset_file = os.path.join(datapath, 'dataset_properties.json')
        data_props = customconfig.Properties(dataset_file)
        if not data_props['to_subfolders']:
            raise NotImplementedError('Scanning only works on datasets organized in subfolders')  # just for simplicity 

        # load body to the scene
        body = utils.load_file(os.path.join(system_config['bodies_path'], data_props['body']), 'body')
        utils.scale_to_cm(body)

        # ------ Main loop --------
        if 'scan_imitation' not in data_props:
            number_of_rays = 30
            number_of_visible_rays = 4
            data_props.set_section_config(
                'scan_imitation', test_rays_num=number_of_rays, visible_rays_num=number_of_visible_rays)
            data_props.set_section_stats('scan_imitation', faces_removed={}, processing_time={})
        if 'fails' not in data_props['scan_imitation']['stats']:
            data_props['scan_imitation']['stats']['fails'] = []
        
        # go over the examples in the data
        start_time = time.time()
        to_ignore = ['renders']  # special dirs not to include in the pattern list
        root, dirs, files = next(os.walk(datapath))  # cannot use os.scandir in python 2.7

        for name in dirs:
            if name not in to_ignore:
                dir_path = os.path.join(root, name)

                # skip if already has a corresponding file
                _, elem_dirs, elem_files = next(os.walk(dir_path))
                if any(['scan_imitation' in filename for filename in elem_files]):
                    print('Datascan::Info::Skipped {} as already processed'.format(name))
                    continue
                
                if not any([name + '_sim.obj' in filename for filename in elem_files]):
                    # simulation result does not exist
                    print('Datascan::Warning::Skipped {} as .obj file does not exist'.format(name))
                    data_props['scan_imitation']['stats']['fails'].append(name)
                    continue
                
                # load mesh
                garment = utils.load_file(os.path.join(dir_path, name + '_sim.obj'), name + '_sim')
                
                # do what we are here for
                removed, time_taken = mymaya.scan_imitation.remove_invisible(
                    garment, [body],
                    data_props['scan_imitation']['config']['test_rays_num'], 
                    data_props['scan_imitation']['config']['visible_rays_num'])
                data_props['scan_imitation']['stats']['faces_removed'][name] = removed
                data_props['scan_imitation']['stats']['processing_time'][name] = time_taken

                # save to original folder
                utils.save_mesh(garment, os.path.join(dir_path, name + '_scan_imitation.obj'))


                data_props.serialize(dataset_file)  # just in case                
                cmds.delete(garment)  # cleanup

        # update props & save
        passed = time.time() - start_time
        data_props.summarize_stats('processing_time', log_sum=True, log_avg=True, as_time=True)
        data_props.summarize_stats('faces_removed', log_avg=True)
        data_props.set_section_stats(
            'scan_imitation', total_processing_time=str(timedelta(seconds=passed))
        )
        
        data_props.serialize(dataset_file)

        print('Scan imitation on {} performed successfully!!!'.format(dataset))

        # clean the scene s.t. next dataset can use another body mesh
        cmds.delete(body)

    # End Maya instance
    stop_mayapy()  # ensures correct exit without errors