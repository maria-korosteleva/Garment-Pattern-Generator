"""
    Run the simulation af a dataset
    Note that it's Python 2.7 friendly
"""
from __future__ import print_function

import simulation as mysim
import utils
reload(mysim)
reload(utils)


if __name__ == "__main__":
    system_config = utils.Properties('./maria_system.json')  # Make sure it's in C:\Autodesk\MayaNNNN\
    path = system_config['templates_path']

    # ------ Dataset Example ------
    dataset_path = system_config['output'] + '/test_skirt_maya_coords_200416-17-14'
    dataset_file = dataset_path + '/dataset_properties.json'
    props = utils.Properties(dataset_file)
    props.set_basic(body='f_smpl_templatex300.obj')

    mysim.batch_sim(path, path, system_config['output'], props)

    props.serialize(dataset_file)

    print(props)

    # ------ Example for single template generation ------
    # props = utils.Properties(path + '/basic_skirt/props.json', True)  
    # mysim.single_file_sim(path, path, props)
    # print(props.properties)
