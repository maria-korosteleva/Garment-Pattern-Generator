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

# Setup
file_keys = [
    'camera_back',
    'camera_front',
    'pattern.svg',
    'pattern.png',
    'specification',
    'sim.obj',
    # 'scan_imitation.obj' sim_segmentation.txt, imitation_segmentation.txt..
]
ignore_fails = True
check_extra = False

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

# gather errors here
missing_files = dict.fromkeys(dataset_folders)
for key in missing_files:
    missing_files[key] = []
extra_files = dict.fromkeys(dataset_folders)
for key in extra_files:
    extra_files[key] = []
size_errors = []
render_errors = []

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

            # check all keys files are present
            for key in file_keys:
                if not any(key in elem for elem in elem_files):
                    if not data_props.is_fail(name):
                        missing_files[dataset].append(name + '_' + key)
                    elif not ignore_fails:
                        missing_files[dataset].append(name + '_' + key + '_fail')
            
            # check if there are some other files present 
            if check_extra:
                for elem in elem_files:
                    if not any(key in elem for key in file_keys):
                        extra_files[dataset].append(name)
        
    # ------- Overall size checks -------
    data_size = data_props['size']
    if data_size != elem_count:
        size_errors.append('{}::ERRRROOOR::Expected {} but got {} datapoints'.format(dataset, data_size, elem_count))

        # missing elements check
        _, fails = data_props.count_fails()
        rendered = list(data_props['render']['stats']['render_time'].keys())
        expected_datapoints = set(rendered + fails)
        for name in dirs:
            if name not in to_ignore:
                expected_datapoints.remove(name)
        
        for elem in expected_datapoints:
            missing_files[dataset].append(elem + '_all')

    else:  # only print the problems
        pass

    # -------- Renders folder check -----------
    if any('renders' in name for name in dirs):
        root, dirs, files = next(os.walk(os.path.join(datapath, 'renders')))  # cannot use os.scandir in python 2.7
        num_renders = len(files)
        num_fails, _ = data_props.count_fails()
        expected_min_num = data_size * 2 - num_fails
        if num_renders != data_size * 2:
            if num_renders >= expected_min_num: 
                render_errors.append('{}::Info:: Num renders {} is less then data size {}, but more then min expectation {}'.format(
                    dataset, num_renders, data_size * 2, expected_min_num))
            else:
                render_errors.append('{}::Warning:: Expected at least {} of {} renders but got {}'.format(
                    dataset, expected_min_num, data_size * 2, num_renders))
    else:
        render_errors.append('{}::Warning::No render folder found'.format(dataset))

# ------- Print final list  ----------
no_size_probelms = []
no_render_problems = []
no_file_problems = []
for dataset in dataset_folders:
    if all([dataset not in elem for elem in size_errors]):
        no_size_probelms.append(dataset)
    if all([dataset not in elem for elem in render_errors]):
        no_render_problems.append(dataset)

print('\nData size check: ')
for error in size_errors:
    print(error)

print('\nRenders check: ')
for error in render_errors:
    print(error)

print('\nFiles missing:')
for dataset in dataset_folders:
    if len(missing_files[dataset]) > 0:
        missing_files[dataset] = sorted(missing_files[dataset])
        print(dataset, ': ')
        for file in missing_files[dataset]:
            print(file)

        print('->')
    else:
        no_file_problems.append(dataset)

if check_extra:
    print('\nExtra files:')
    for dataset in dataset_folders:
        if len(extra_files[dataset]) > 0:
            extra_files[dataset] = sorted(extra_files[dataset])
            print(dataset, ': ')
            for file in extra_files[dataset]:
                print(file)

            print('->')


# ----- Success ------
no_problems = [d for d in dataset_folders if d in no_size_probelms and d in no_render_problems and d in no_file_problems]
print('\nEverything OK: ')
print(*no_problems, sep='\n')

# print('\nData size OK: ')
# print(no_size_probelms)

# print('\nRenders OK: ')
# print(no_render_problems)

# print('\nFiles OK:')
# print(no_file_problems)