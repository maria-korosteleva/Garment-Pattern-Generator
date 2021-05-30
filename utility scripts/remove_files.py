import shutil
import os
import customconfig
from PIL import Image

dataset_list = [
    # 'test_150_dress_210401-17-57-12',
    # 'test_150_jacket_hood_sleeveless_210331-11-16-33',
    # 'test_150_jacket_sleeveless_210331-15-54-26',
    # 'test_150_jumpsuit_210401-16-28-21',
    # 'test_150_skirt_waistband_210331-16-05-37',
    # 'test_150_tee_hood_210401-15-25-29',
    # 'test_150_wb_jumpsuit_sleeveless_210404-11-27-30'
    
    'merged_dress_sleeveless_2550_210429-13-12-52',
    'merged_jumpsuit_sleeveless_2000_210429-11-46-14',
    'merged_skirt_8_panels_1000_210521-16-20-14', # has fails
    'merged_wb_pants_straight_1500_210521-16-30-57',
    'merged_skirt_2_panels_1200_210521-16-46-27',
    'merged_jacket_2200_210521-16-55-26',
    'merged_tee_sleeveless_1800_210521-17-10-22',
    'merged_wb_dress_sleeveless_2600_210521-17-26-08',  # had fails
    'merged_jacket_hood_2700_210521-17-47-44'
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




            
