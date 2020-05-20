"""
    Run the simulation af a dataset
    Note that it's Python 2.7 friendly
"""
from __future__ import print_function
import os
import errno

try: 
    import maya.standalone 			
    maya.standalone.initialize()
    cmds.loadPlugin('mtoa.mll')  # https://stackoverflow.com/questions/50422566/how-to-register-arnold-render
    cmds.loadPlugin('objExport.mll')  # same as in https://forums.autodesk.com/t5/maya-programming/invalid-file-type-specified-atomimport/td-p/9121166
except Exception as e: 
    print(e) 			
    pass

# My modules
import mayaqltools as mymaya
import customconfig
reload(mymaya)
reload(customconfig)


if __name__ == "__main__":
    system_config = customconfig.Properties('../system.json')  # Make sure it's in \Autodesk\MayaNNNN\
    path = system_config['templates_path']

    # ------ Dataset Example ------
    dataset = 'data_150_tee_200515-15-31-40-fast_sim'
    datapath = os.path.join(system_config['output'], dataset)
    dataset_file = os.path.join(datapath, 'dataset_properties.json')

    # defining sim props
    props = customconfig.Properties(dataset_file)
    props.set_basic(data_folder=dataset)   # in case data properties are from other dataset/folder, update info
    # props.merge(os.path.join(system_config['sim_configs_path'], 
    #                         'sim_props_good_render_basic_body.json'))

    mymaya.simulation.batch_sim(system_config, datapath, props, caching=False, force_restart=False)
    props.serialize(dataset_file)

    # ------ Example for single template generation ------
    # path_example = os.path.join(system_config['output'], 'from_editor', 'deactive_200430-15-42-02')
    # # props = customconfig.Properties(path_example + '/dataset_properties.json', True)  
    # props = customconfig.Properties(os.path.join(path_example, 'sim_props.json'), True)  
    # props.set_basic(
    #     body='f_smpl_templatex300.obj',
    #     templates='skirt_maya_coords_specification.json'
    # )
    # mymaya.simulation.single_file_sim(system_config, props, caching=False)
    # print(props)
