"""
    Check is all the needed files are present (recommended check after dataset download)
"""

from __future__ import print_function
import os
import time
from datetime import timedelta
from pathlib import Path

# My modules
import customconfig
# reload in case we are in Maya internal python environment

system_config = customconfig.Properties('system.json')  # Make sure it's in \Autodesk\MayaNNNN\
path = Path(system_config['datasets_path'])

# ------ Datasets ------
dataset_folders = []

for child in path.iterdir():
    if child.is_dir() and child.name != 'Archive' and child.name != 'test':
        dataset_folders.append(child.name)
    if child.is_dir() and child.name == 'test':
        for nested_child in child.iterdir():
            if child.is_dir() and child.name != 'Archive':
                dataset_folders.append('test/' + nested_child.name)

print(dataset_folders)

file_keys = [
    'camera_back',
    'camera_front',
    'pattern.svg',
    'pattern.png',
    'specification',
    'sim.obj',
    # 'scan_imitation.obj'
]

missing_files = dict.fromkeys(dataset_folders)
for key in missing_files:
    missing_files[key] = []

for dataset in dataset_folders:
    datapath = os.path.join(system_config['datasets_path'], dataset)
    # print(datapath)
    dataset_file = os.path.join(datapath, 'dataset_properties.json')
    data_props = customconfig.Properties(dataset_file)

    # ----- Missing files ---------
    to_ignore = ['renders']  # special dirs not to include in the pattern list
    root, dirs, files = next(os.walk(datapath))  # cannot use os.scandir in python 2.7

    # per element checks
    elem_count = 0
    for name in dirs:
        if name not in to_ignore:
            dir_path = os.path.join(root, name)
            elem_count += 1
            # print(name)

            _, elem_dirs, elem_files = next(os.walk(dir_path))

            for key in file_keys:
                if not any(key in elem for elem in elem_files):
                    if not data_props.is_fail(name):
                        missing_files[dataset].append(name + '_' + key)
                    else:
                        missing_files[dataset].append(name + '_' + key + '_fail')
        
    # ------- Overall size check -------
    data_size = data_props['size']
    if data_size != elem_count:
        print('{}::ERRRROOOR::Expected {} but got {} datapoints'.format(dataset, data_size, elem_count))
    else:  # only print the problems
        pass
    
    # -------- Renders folder check -----------
    if any('renders' in name for name in dirs):
        root, dirs, files = next(os.walk(os.path.join(datapath, 'renders')))  # cannot use os.scandir in python 2.7
        num_renders = len(files)
        if num_renders != data_size * 2:
            print('{}::Warning:: Expected {} renders but got {}'.format(dataset, data_size * 2, num_renders))
    else:
        print('{}::Warning::No render folder found'.format(dataset))

# No need to pay attention to correct datasets
print('Files missing:')
for dataset in dataset_folders:
    if len(missing_files[dataset]) > 0:
        print(dataset, ': ')
        for file in missing_files[dataset]:
            print(file)

        print('->')
