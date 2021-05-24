import shutil
import os
import customconfig
from PIL import Image

dataset_list = [
    'data_1000_skirt_4_panels_200616-14-14-40'
]

file_keys_remove = [
    'scene.mb',
    '_stitched.obj'
]

removed = dict.fromkeys(dataset_list, 0)

system_props = customconfig.Properties('./system.json')

for dataset in dataset_list:
    datapath = os.path.join(system_props['datasets_path'], dataset)

    for root, dirs, files in os.walk(datapath):
        for filename in files:
            if any(key in filename for key in file_keys_remove):
                try:
                    if os.path.exists(os.path.join(root, filename)):
                        removed[dataset] += 1
                        print(filename) 
                        os.remove(os.path.join(root, filename))
                except Exception as e:
                        print(e)

for key, num in removed.items():
    print('{}: {}'.format(key, num))




            
