"""
    When the dataset simulation process was severely disrupted and a lot of datapoints marked as crashes, 
    it's useful to try to re-simulate failed examples only.

    This script marks the crashed datapoints as unprocessed for a given dataset folder. After that, 
    batch simulation can be started over.

    NOTE: this simple script only works correctly on the datasets for which the batch simulation has finalized 
    (no 'processed' key is present in dataset.properties.json)
"""


from pathlib import Path
import customconfig
from pattern.wrappers import VisPattern

dataset = 'data_1050_jacket_hood_210415-17-01-48'

system_props = customconfig.Properties('./system.json')
datapath = Path(system_props['datasets_path']) / dataset

print(datapath)

dataprops = customconfig.Properties(datapath / 'dataset_properties.json')

if 'processed' in dataprops['sim']['stats'] and len(dataprops['sim']['stats']['processed']) > 0:
    raise RuntimeError('This script is only applicable to datasets for which sim processing finished.')

dataprops.serialize(datapath / 'dataset_properties_with_crashes.json')

dataprops['sim']['stats']['processed'] = []
crashes = dataprops['sim']['stats']['fails']['crashes']

for child in datapath.iterdir():
    if child.is_dir() and child.name != 'renders':
        if child.name not in crashes:
            dataprops['sim']['stats']['processed'].append(child.name)


dataprops['sim']['stats']['fails']['crashes'] = []

dataprops['frozen'] = False

dataprops.serialize(datapath / 'dataset_properties.json')


