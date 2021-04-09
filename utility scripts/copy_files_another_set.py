from pathlib import Path
import json
import customconfig
import shutil
from pattern.wrappers import VisPattern

dataset_out = 'data_5000_skirt_4_panels_201019-12-23-24_regen_210331-16-18-32'
dataset_in = 'Archive/data_5000_skirt_4_panels_201019-12-23-24'

system_props = customconfig.Properties('./system.json')
datapath_out = Path(system_props['datasets_path']) / dataset_out
datapath_in = Path(system_props['datasets_path']) / dataset_in

print(datapath_in)
print(datapath_out)

for child in datapath_in.iterdir():
    if child.is_dir() and child.name != 'renders':
        print(child.name)
        for elem in child.iterdir():
            if (elem.is_file() and 
                    ('sim.obj' in elem.name or 'camera' in elem.name)):
                try: 
                    #print (str(elem))
                    #print (str(datapath_out / child.name / elem.name))
                    shutil.copy(str(elem), datapath_out / child.name / elem.name)
                except shutil.SameFileError:
                    print('File {} already exists'.format(elem))
                    pass

