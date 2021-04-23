from pathlib import Path
import customconfig
from pattern.wrappers import VisPattern

dataset = 'data_1050_jacket_hood_210415-17-01-48'

system_props = customconfig.Properties('./system.json')
datapath = Path(system_props['datasets_path']) / dataset

print(datapath)

dataprops = customconfig.Properties(datapath / 'dataset_properties.json')

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


