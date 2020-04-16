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

    props = utils.Properties(path + '/basic_skirt/props.json', True)
    # props.set_basic(
    #     templates='basic_skirt/skirt_maya_coords.json',
    #     name='props_style',
    #     body='f_smpl_templatex300.obj'  # in templates folder -- for now
    # )
  
    mysim.single_file_sim(path, path, props)

    print(props.properties)
