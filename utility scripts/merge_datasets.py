"""
    Merge two datafolders that were produced from the same template into one folder, 
    with single dataset_properties.json for the merged folder.

    For keeping the data organized by base garment type.
"""

from datetime import datetime
import shutil
import os
from pathlib import Path

# My
import customconfig


def copy_files_subfolders(from_dataset, merged_folder, original_name=''):
    """
        Copy contents of initial dataset to the new folder
    """
    for child in from_dataset.iterdir():
        if child.is_dir():  # go one layer deeper
            for elem in child.iterdir():
                try:
                    new_dir = merged_folder / child.name
                    new_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy(str(elem), merged_folder / child.name / elem.name)
                except shutil.SameFileError:
                    print('Child {} / {} already exists'.format(child.name, elem.name))
                    pass
        elif 'template' in child.name:  # no need for additional naming of the template files
            try:
                shutil.copy(str(child), merged_folder / child.name)
            except shutil.SameFileError:
                print('Child {} already exists'.format(child))
                pass
        else:
            # print(child.name)
            try:
                shutil.copy(str(child), merged_folder / (original_name + '_' + child.name))
            except shutil.SameFileError:
                print('Child {} already exists'.format(child))
                pass
                    


system_props = customconfig.Properties('./system.json')
datasets = [
    'merged_dress_sleeveless_1350_210422-11-26-50',
    'data_1200_dress_sleeveless_210426-11-56-1']
data_root = Path(system_props['datasets_path']) 
output_root = Path(system_props['datasets_path']) 

props = []
for folder in datasets:
    props.append(customconfig.Properties(Path(system_props['datasets_path']) / folder / 'dataset_properties.json'))

# 0. validity checks
if len(datasets) < 2:
    raise NotImplementedError('Need 2 or more datasetsto merge')
base_template = props[0]['templates']
for prop in props:
    if prop['templates'] != base_template:
        raise ValueError('Merging is only allowed on datasets derived from the same template')

# 1. Create new folder
merged_name = 'merged_' + base_template.split('/')[1].split('.')[0]
merged_size = sum([prop['size'] for prop in props])
new_folder_name = merged_name + '_' + str(merged_size) + '_' + datetime.now().strftime('%y%m%d-%H-%M-%S')
merged_data_folder = output_root / new_folder_name
merged_data_folder.mkdir(parents=True)

# 2. Merge props
merged_props = customconfig.Properties(data_root / datasets[0] / 'dataset_properties.json')
for i in range(1, len(datasets)):
    merged_props.merge(
        data_root / datasets[i] / 'dataset_properties.json',
        re_write=False, 
        adding_tag=props[i]['name'])

# Recalucalate some fields
merged_props['name'] = merged_name
merged_props['data_folder'] = new_folder_name
merged_props['size'] = merged_size
# Update stats calculations 
merged_props.stats_summary()
# save new props
merged_props.serialize(merged_data_folder / 'dataset_properties.json')

# 3. sim_outputs merging & copy
with open(merged_data_folder / 'sim_output.txt', 'wb') as outfile:
    for dataset in datasets:
        try:
            with open(data_root / dataset / 'sim_output.txt', 'rb') as read_sim:
                shutil.copyfileobj(read_sim, outfile)
        except IOError as e:  # e.g. file doesn't exist
            print(e)
            print('Continuing anyway...')

# 4. Copy files & subfolders
for i in range(len(datasets)):
    copy_files_subfolders(data_root / datasets[i], merged_data_folder, props[i]['name'])


# ------------------------
