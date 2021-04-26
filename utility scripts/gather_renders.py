"""In simulated dataset, gather all the scene images in one folder"""

import shutil
import os
import customconfig

dataset = 'data_1250_jacket_210414-15-48-45'

system_props = customconfig.Properties('./system.json')
datapath = os.path.join(system_props['datasets_path'], dataset)
renders_path = os.path.join(datapath, 'renders')

os.makedirs(renders_path, exist_ok=True)

for root, dirs, files in os.walk(datapath):
    for filename in files:
        if 'camera' in filename and 'renders' not in root:
            try: 
                shutil.copy(os.path.join(root, filename), renders_path)
            except shutil.SameFileError:
                print('File {} already exists'.format(filename))
                pass
