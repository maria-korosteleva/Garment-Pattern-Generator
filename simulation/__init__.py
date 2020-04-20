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
def single_file_sim(template_path, body_path, props, caching=False):
    """
        Simulates the given template and puts the results in original template folder, 
        including config and statistics
    """
    try:
        # ----- Init -----
        _init_sim_props(props, True)
        qw.load_plugin()
        scene = mayasetup.Scene(body_path + '/' + props['body'], props['render'])

        # Main part
        _template_simulation(template_path + '/' + props['templates'], 
                             scene, 
                             props['sim'], 
                             caching=caching)

        # Fin
        print('Finished experiment')
        try:
            # remove unnecessaty field
            del props['sim']['stats']['processed']
        except KeyError:
            pass
        props.serialize(os.path.dirname(template_path + '/' + props['templates']) + '/props.json')
    except Exception as e:
        print(e)


def batch_sim(template_path, body_path, data_path, dataset_props, 
              caching=False, force_restart=False):
    """
        Performs pattern simulation for each example in the dataset 
        given by dataset_props. 
        Batch processing is automatically resumed 
        from the last unporcessed datapoint if restart is not forced. The last 
        example on the processes list is assumed to cause the failure, so it can be later found in failure cases. 

        Parameters:
            * template_path -- path to folder with pattern templates
            * body_path -- path to folder with body meshes
            * data_path -- path to folder with datasets
            * dataset_props -- dataset properties. Properties has to be of custom customconfig.Properties() class and contain
                    * dataset folder (inside data_path) 
                    * name of pattern template
                    * name of body .obj file
                    * type of dataset structure (with/without subfolders for patterns)
                Other needed properties will be filles with default values if the corresponding sections
                are not found in props object
            * caching -- enables caching of every frame of simulation (disabled by default)
            * force_restart -- force restarting the batch processing even if resume conditions are met. 
        
    """
    # ----- Init -----
    resume = _init_sim_props(dataset_props, force_restart)
    qw.load_plugin()
    scene = mayasetup.Scene(body_path + '/' + dataset_props['body'], dataset_props['render'])
    pattern_specs = _get_pattern_files(data_path, dataset_props)
    data_props_file = os.path.join(data_path, dataset_props['data_folder'], 'dataset_properties.json')

    # Simulate every template
    for pattern_spec in pattern_specs:
        # skip processed cases -- in case of resume. First condition needed to skip checking second one on False =) 
        if resume and pattern_spec in dataset_props['sim']['stats']['processed']:
            continue
        dataset_props['sim']['stats']['processed'].append(pattern_spec)
        dataset_props.serialize(data_props_file)  # save info of processed files before potential crash

        _template_simulation(pattern_spec, 
                             scene, 
                             dataset_props['sim'], 
                             delete_on_clean=True,  # delete geometry after sim s.t. it doesn't resim with each new example
                             caching=caching)  

    # Fin
    print('Finished ' + dataset_props['data_folder'])
    try:
        # processing successfully finished -- no need to resume later
        del dataset_props['sim']['stats']['processed']
    except KeyError:
        pass

    dataset_props.serialize(data_props_file)


# ------- Utils -------
def _init_sim_props(props, force_restart):
    """ 
        Add default config values if not given in props & clean-up stats if not resuming previous processing
        Returns a flag wheter current simulation is a resumed last one
    """
    if 'sim' not in props:
        props.set_section_config(
            'sim', 
            max_sim_steps=500, 
            zero_gravity_steps=5,  # time to assembly 
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
    
    if force_restart or 'processed' not in props['sim']['stats']:  # new life
        # Prepare commulative stats
        props.set_section_stats(
            'sim', 
            sim_fails=[], 
            sim_time=[], 
            spf=[], 
            fin_frame=[], 
            processed=[])

        props.set_section_stats(
            'render', 
            render_time=[]
        )
        resume = False
    else:
        # resuming existing batch processing -- do not clean stats 
        # Assuming the last example processed example caused the failure
        props['sim']['stats']['sim_fails'].append(props['sim']['stats']['processed'][-1])
        resume = True
    return resume
        

def _template_simulation(spec, scene, sim_props, delete_on_clean=False, caching=False):
    """
        Simulate given template withing given scene & save log files
    """
    garment = mayasetup.MayaGarment(spec)
    garment.load()
    garment.setMaterialProps(scene.cloth_shader)
    garment.add_colliders(scene.body)  # I don't add floor s.t. garment falls infinitely if falls
    garment.sim_caching(caching)

    qw.run_sim(garment, sim_props)

    # save even if sim failed -- to see what happened!
    garment.save_mesh()
    scene.render(garment.path, garment.name + '_scene')

    garment.clean(delete_on_clean)


def _get_pattern_files(data_path, dataset_props):
    """ Collects paths to all the pattern files in given folder"""

    dataset_path = os.path.join(data_path, dataset_props['data_folder'])
    pattern_specs = []
    root, dirs, files = next(os.walk(dataset_path))
    if dataset_props['to_subfolders']:
        # https://stackoverflow.com/questions/800197/how-to-get-all-of-the-immediate-subdirectories-in-python
        # cannot use os.scandir in python 2.7
        for directory in dirs:
            pattern_specs.append(os.path.join(root, directory, 'specification.json'))  # cereful for file name changes ^^
    else:
        for file in files:
            # NOTE filtering might not be very robust
            if ('.json' in file
                    and 'template' not in file
                    and 'dataset_properties' not in file):
                pattern_specs.append(os.path.join(root, file))
    return pattern_specs
