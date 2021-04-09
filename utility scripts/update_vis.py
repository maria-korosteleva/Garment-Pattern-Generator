from pathlib import Path
import customconfig
from pattern.wrappers import VisPattern

dataset = 'data_uni_20_pants_straight_sides_210304-13-38-10'

system_props = customconfig.Properties('./system.json')
datapath = Path(system_props['datasets_path']) / dataset

print(datapath)

for child in datapath.iterdir():
    if child.is_dir() and child.name != 'renders':
        for elem in child.iterdir():
            if elem.is_file() and elem.name == 'specification.json':
                pattern = VisPattern(str(elem), view_ids=False)
                pattern._save_as_image(str(child / '_pattern.svg'), str(child / '_pattern.png'))
                print(child)


