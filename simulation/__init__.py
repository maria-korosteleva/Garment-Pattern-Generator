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

# My modules
from simulation import mayasetup
from simulation import qualothwrapper as qw
reload(mayasetup)
reload(qw)


# ----------- Main loop --------------
def single_file_sim(template_path, body_path, props):
    """
        Simulates the given template and puts the results in original template folder, 
        including config and statistics
    """
    try:
        # ----- Init -----
        if 'sim' not in props:
            # init with defaults
            props.set_section_config(
                'sim', 
                max_sim_steps=30, 
                min_sim_steps=10,  # no need to check for static equilibrium until min_steps 
                static_threshold=0.05  # 0.01  # depends on the units used
            )
        props.set_section_stats(
            'sim', 
            sim_fails=[], 
            sim_time=[], 
            spf=[], 
            fin_frame=[])
        
        if 'render' not in props:
            # init with defaults
            props.set_section_config(
                'render',
                body_color=[0.5, 0.5, 0.7], 
                cloth_color=[0.8, 0.2, 0.2],
                floor_color=[0.8, 0.8, 0.8],
                resolution=[800, 800]
            )

        qw.load_plugin()

        scene = mayasetup.Scene(body_path + '/' + props['body'], props['render'])

        # --- future loop of batch processing ---
        garment = mayasetup.MayaGarment(template_path + '/' + props['templates'])
        garment.load()
        garment.setMaterialProps(scene.cloth_shader)
        garment.add_colliders(scene.body)  # I don't add floor s.t. garment falls infinitely if falls

        qw.run_sim(garment, props['sim'])

        # save even if sim failed -- to see what happened!
        garment.save_mesh()
        scene.render(garment.path)

        garment.clean()
        # -------- Fin loop --------
        print('Finished experiment')
        props.serialize(garment.path + '/props.json')
    except Exception as e:
        print(e)
