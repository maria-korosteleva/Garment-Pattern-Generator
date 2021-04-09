import shutil
import os
import customconfig
from PIL import Image

dataset = 'data_1000_skirt_4_panels_200616-14-14-40'

system_props = customconfig.Properties('./system.json')
datapath = os.path.join(system_props['datasets_path'], dataset)

for root, dirs, files in os.walk(datapath):
    for filename in files:
        if 'scene.mb' in filename:
            try:
                if os.path.exists(os.path.join(root, filename)):
                    print(filename) 
                    os.remove(os.path.join(root, filename))
            except Exception as e:
                    print(e)





            
