"""
    Package for to simulate garments from patterns in Maya with Qualoth
    Note that Maya uses Python 2.7 (incl Maya 2020) hence this module is adapted to Python 2.7

    Main dependencies:
        * Maya 2018+
        * Arnold Renderer
        * Qualoth (compatible with your Maya version)
    
    To run the package in Maya don't foget to add it to PYTHONPATH!
"""

# Basic
from __future__ import print_function
import time
import os

# My modules
from simulation import mayasetup
from simulation import qualothwrapper as qw
reload(mayasetup)
reload(qw)


# ----------- single file sim for testing --------------
def single_file_sim(template_path, body_path, props):
    """
        Simulates the given template and puts the results in original template folder, 
        including config and statistics
    """
    try:
        # ----- Init -----
        _init_sim_props(props)
        qw.load_plugin()
        scene = mayasetup.Scene(body_path + '/' + props['body'], props['render'])

        # Main part
        _template_simulation(template_path + '/' + props['templates'], 
                             scene, 
                             props['sim'])

        # Fin
        print('Finished experiment')
        props.serialize(os.path.dirname(template_path + '/' + props['templates']) + '/props.json')
    except Exception as e:
        print(e)


def batch_sim(template_path, body_path, data_path, dataset_props):
    """
        Performs pattern simulation for each example in the dataset 
        given by dataset_props
        Properties has to be of custom utils.Properties() class and contain
            * dataset folder (inside data_path) 
            * name of pattern template
            * name of body .obj file
            * type of dataset structure (with/without subfolders for patterns)
        Other needed properties will be filles with default values if the corresponding sections
        are not found in props object
    """
    # ----- Init -----
    _init_sim_props(dataset_props)
    qw.load_plugin()
    scene = mayasetup.Scene(body_path + '/' + dataset_props['body'], dataset_props['render'])

    # get files
    dataset_path = os.path.join(data_path, dataset_props['data_folder'])
    if dataset_props['to_subfolders']:
        # https://stackoverflow.com/questions/800197/how-to-get-all-of-the-immediate-subdirectories-in-python
        # cannot use os.scandir in python 2.7
        pattern_specs = []
        root, dirs, _ = next(os.walk(dataset_path))
        for directory in dirs:
            pattern_specs.append(os.path.join(root, directory, 'specification.json'))
    else:
        pattern_specs = []
        for file in os.scandir(data_path):
            # NOTE filtering might not be very robust
            if (not file.is_dir() and '.json' in file.name
                    and 'template' not in file.name 
                    and 'dataset_properties' not in file.name):
                pattern_specs.append[file.path]

    # Simulate every template
    for pattern_spec in pattern_specs:
        _template_simulation(pattern_spec, 
                             scene, 
                             dataset_props['sim'], 
                             True)  # delete geometry after sim s.t. it doesn't resim with each new example

    # Fin
    print('Finished ' + dataset_props['data_folder'])


# ------- Utils -------
def _init_sim_props(props):
    """ Add default config values if not given in props & clean-up stats"""
    if 'sim' not in props:
        props.set_section_config(
            'sim', 
            max_sim_steps=500, 
            min_sim_steps=10,  # no need to check for static equilibrium until min_steps 
            static_threshold=0.05  # 0.01  # depends on the units used
        )

    if 'render' not in props:
        # init with defaults
        props.set_section_config(
            'render',
            body_color=[0.5, 0.5, 0.7], 
            cloth_color=[0.8, 0.2, 0.2],
            floor_color=[0.8, 0.8, 0.8],
            resolution=[800, 800]
        )
    
    # Prepare commulative stats
    props.set_section_stats(
        'sim', 
        sim_fails=[], 
        sim_time=[], 
        spf=[], 
        fin_frame=[])
    
    props.set_section_stats(
        'render', 
        render_time=[]
    )


def _template_simulation(spec, scene, sim_props, delete_on_clean=False):
    """
        Simulate given template withing given scene & save log files
    """
    garment = mayasetup.MayaGarment(spec)
    garment.load()
    garment.setMaterialProps(scene.cloth_shader)
    garment.add_colliders(scene.body)  # I don't add floor s.t. garment falls infinitely if falls

    qw.run_sim(garment, sim_props)

    # save even if sim failed -- to see what happened!
    garment.save_mesh()
    scene.render(garment.path, garment.name + '_scene')

    garment.clean(delete_on_clean)
