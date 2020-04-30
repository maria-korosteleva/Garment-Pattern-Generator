"""
    Run the simulation af a dataset
    Note that it's Python 2.7 friendly
"""
from __future__ import print_function
import os


# My modules
import mayaqltools as mymaya
import customconfig
reload(mymaya)
reload(customconfig)


if __name__ == "__main__":
    system_config = customconfig.Properties('./system.json')  # Make sure it's in \Autodesk\MayaNNNN\
    path = system_config['templates_path']

    # ------ Dataset Example ------
    dataset = 'deactive_skirt_maya_coords_200430-15-58-24'
    datapath = os.path.join(system_config['output'], dataset)
    dataset_file = os.path.join(datapath, 'dataset_properties.json')
    props = customconfig.Properties(dataset_file)
    props.set_basic(
        body='f_smpl_templatex300.obj', 
        data_folder=dataset  # in case data properties are from other dataset/folder, update info
    )  

    mymaya.simulation.batch_sim(path, path, datapath, props, caching=False)
    props.serialize(dataset_file)

    # ------ Example for single template generation ------
    # path_example = os.path.join(system_config['output'], 'from_editor', 'deactive_200430-15-42-02')
    # # props = customconfig.Properties(path_example + '/dataset_properties.json', True)  
    # props = customconfig.Properties(os.path.join(path_example, 'sim_props.json'), True)  
    # props.set_basic(
    #     body='f_smpl_templatex300.obj',
    #     templates='skirt_maya_coords_specification.json'
    # )
    # # TODO Give path to template directly
    # mymaya.simulation.single_file_sim(path_example, path, props, caching=False)
    # print(props)
