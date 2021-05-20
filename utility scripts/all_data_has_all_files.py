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
dataset_folders = [
    'data_1000_jacket_hood_210430-15-12-19',
    'merged_jacket_hood_1700_210425-21-23-19',
    'data_650_tee_sleeveless_210429-10-55-00',
    'data_650_jacket_210504-11-07-51',
    ''
]

dataset_folders = []

for child in path.iterdir():
    if child.is_dir():
        dataset_folders.append(child.name)

print(child)

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

    # ------ Main loop --------        
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
            

    # Top checks
    data_size = data_props['size']
    if data_size != elem_count:
        print('{}::ERRRROOOR::Expected {} but got {} datapoints'.format(dataset, data_size, elem_count))
    else:
        print('{}::Datapoints count is correct: {}'.format(dataset, elem_count))

# No need to pay attention to correct datasets
print('Files missing:')

for dataset in dataset_folders:
    if len(missing_files[dataset]) > 0:
        print(dataset, ': ')
        for file in missing_files[dataset]:
            print(file)

        print('->')
