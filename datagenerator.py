# Libs
from pathlib import Path
from datetime import datetime
import time
import json
import os
import random
import shutil

# My module
import pattern


class DatasetProperties():
    """Keeps loads, and saves properties of a synthetic dataset.
        Objects of the class can be treated as dictionaries.
        Mandatory properties include
            * size (number of datapoints)
            * template (name of template file which variation forms a datapoint)
            * random_seed (for reproducibility)
            * to_subfolders (whether each datapoint is stored in a separate subfolder)
            * name (of a current dataset)
    """
    def __init__(self, template_names, size, 
                 data_to_subfolders=True, name="", random_seed=None):
        self.properties = {}
        # Init mandatory dataset properties
        self['size'] = size
        self['templates'] = template_names
        self['to_subfolders'] = data_to_subfolders
        self['name'] = name
        if random_seed is None:
            self['random_seed'] = int(time.time())  # new random seed
        else:
            self['random_seed'] = random_seed
    
    @classmethod
    def fromfile(cls, prop_file):
        with open(prop_file, 'r') as f_json:
            props = json.load(f_json) 
        if 'data_folder' in props:
            # props of the previous dataset
            props['name'] = props['data_folder'] + '_regen'

        return cls(props['templates'], 
                   props['size'],
                   props['to_subfolders'], 
                   props['name'],
                   props['random_seed'])

    def __getitem__(self, key):
        return self.properties[key]

    def __setitem__(self, key, value):
        self.properties[key] = value
    
    def serialize(self, filename):
        with open(filename, 'w') as f_json:
            json.dump(self.properties, f_json, indent=2)


def generate(path, templates_path, props):
    """Generates a synthetic dataset of patterns with given properties
        Params:
            path : path to folder to put a new dataset into
            templates_path : path to folder with pattern templates
            props : an instance of DatasetProperties class
                    requested properties of the dataset
        Not Implemented: 
            * Generation from multiple template patterns
            * Physics simulation of garments
    """
    path = Path(path)
    # TODO modify to support multiple templates
    if isinstance(props['templates'], list):
        raise NotImplemented('Generation from multiple templates is not supported')
    template_file_path = Path(templates_path) / props['templates']

    # create data folder
    data_folder = props['name'] + '_' + template_file_path.stem + '_' \
        + datetime.now().strftime('%y%m%d-%H-%M')
    props['data_folder'] = data_folder
    path_with_dataset = path / data_folder
    os.makedirs(path_with_dataset)
    # Copy template for convernience TODO copy with visualization? 
    shutil.copyfile(template_file_path, 
                    path_with_dataset / ('template_' + template_file_path.name))

    # init random seed
    random.seed(props['random_seed'])

    # generate data
    start_time = time.time()
    for _ in range(props['size']):
        new_pattern = pattern.RandomPatternWrapper(template_file_path)
        new_pattern.serialize(path_with_dataset, 
                              to_subfolder=props['to_subfolders'])
    elapsed = time.time() - start_time
    props['generation_time'] = f'{elapsed:.3f} s'

    # log properties
    props.serialize(path_with_dataset / 'dataset_properties.json')


# ------------------ MAIN ------------------------
if __name__ == "__main__":
    
    new = True

    if new:
        props = DatasetProperties(
            'skirt_per_panel.json', 
            size=10,
            data_to_subfolders=False, 
            name='random_class')
    else:
        props = DatasetProperties.fromfile(
            'F:/GK-Pattern-Data-Gen/N_skirt_per_panel_200324-17-22/dataset_properties.json')

    # Generator
    generate('F:/GK-Pattern-Data-Gen/', './Patterns', props)
