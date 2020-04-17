"""
    Run the simulation af a dataset
    Note that it's Python 2.7 friendly
"""
from __future__ import print_function

import simulation as mysim
import customconfig
reload(mysim)
reload(customconfig)


if __name__ == "__main__":
    system_config = customconfig.Properties('./system.json')  # Make sure it's in \Autodesk\MayaNNNN\
    path = system_config['templates_path']

    # ------ Dataset Example ------
    dataset_path = system_config['output'] + '/test_skirt_maya_coords_200417-10-18-Copy'
    dataset_file = dataset_path + '/dataset_properties.json'
    props = customconfig.Properties(dataset_file)
    props.set_basic(body='f_smpl_templatex300.obj')

    mysim.batch_sim(path, path, system_config['output'], props)
    props.serialize(dataset_file)

    # ------ Example for single template generation ------
    # props = utils.Properties(path + '/basic_skirt/props.json', True)  
    # props['templates'] = 'specification.json'
    # path_example = 'F:/GK-Pattern-Data-Gen/test_skirt_maya_coords_200416-17-16-copy/skirt_maya_coords_5H2GM5649T'
    # # TODO Give path to template directly
    # mysim.single_file_sim(path_example, path, props)
    # print(props)
