from pathlib import Path
import json
import customconfig
from pattern.wrappers import VisPattern

dataset_out = 'data_uni_1000_tee_200527-14-50-42_regen_200612-16-56-43'

system_props = customconfig.Properties('./system.json')
datapath_out = Path(system_props['datasets_path']) / dataset_out

print(datapath_out)

for child in datapath_out.iterdir():
    if child.is_dir() and child.name != 'renders':
        print(child.name)
        for elem in child.iterdir():
            if elem.is_file() and elem.name == 'specification.json':
                with open(elem, 'r') as f_json:
                    spec = json.load(f_json)
                
                spec['pattern']['panel_order'] =[ "rbsleeve", "rfsleeve", "back", "front", "lbsleeve", "lfsleeve" ]  # TEEES!!!!   

                with open(elem, 'w') as f_json:
                    json.dump(spec, f_json, indent=2)

