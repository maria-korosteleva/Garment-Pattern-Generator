"""In simulated dataset, gather all the scene images in one folder"""

import shutil
import os
import customconfig

datasets = [ 
    'jacket_hood_2700',
    'dress_sleeveless_2550',
    'jacket_2200',
    'jumpsuit_sleeveless_2000',
    'pants_straight_sides_1000',
    'skirt_2_panels_1200',
    'skirt_4_panels_1600',
    'skirt_8_panels_1000',
    'tee_2300',
    'wb_pants_straight_1500',
    'test/jacket_hood_sleeveless_150',
    'test/jacket_sleeveless_150' ,
    'test/jumpsuit_150' ,
    'test/skirt_waistband_150', 
    'test/wb_jumpsuit_sleeveless_150' 
]

system_props = customconfig.Properties('./system.json')
for dataset in datasets:
    datapath = os.path.join(system_props['datasets_path'], dataset)
    datapath = 'D:/MyDocs/GigaKorea/NeurIPS21 Submission/all_templates/Test group'
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
