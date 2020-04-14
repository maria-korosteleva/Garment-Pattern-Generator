"""
    Package for to simulate garments from patterns in Maya with Qualoth
    Note that Maya uses Python 2.7 (incl Maya 2020) hence this module is adapted to Python 2.7

    Main dependencies:
        * Maya 2018+
        * Qualoth (compatible with your Maya version)
    
    To run custom packages in Maya don't foget to add them to PYTHONPATH
"""

# Basic
from __future__ import print_function
import time

# My modules
import mayasetup
import qualothwrapper as qw
reload(mayasetup)
reload(qw)


# ----------- Main loop --------------
def single_file_sim(pattern_json_file, body_path, save_to):
    try:
        # ----- Init -----
        options = {
            'body': body_path,
            'sim': {
                'max_sim_steps': 1500, 
                'min_sim_steps': 10,  # no need to check for static equilibrium until min_steps 
                'sim_fails': [], 
                'static_threshold': 0.05  # 0.01  # depends on the units used
            },
            'render': {
                'body_color': [0.1, 0.2, 0.7], 
                'cloth_color': [0.8, 0.2, 0.2],
                'floor_color': [0.1, 0.1, 0.1],
                'resolution': [800, 800]
            }
            
        }
        qw.load_plugin()

        scene = mayasetup.Scene(options['body'], options['render'])

        # --- future loop of batch processing ---
        garment = mayasetup.MayaGarment(pattern_json_file)
        garment.load()
        garment.setMaterialProps(scene.cloth_shader)
        garment.add_colliders(scene.body, scene.floor)

        qw.run_sim(garment, options['sim'])

        # save even if sim failed -- to see what happened!
        garment.save_mesh(save_to)
        scene.render(save_to)

        garment.clean()
        # -------- Fin loop --------

        print('Finished experiment')
        # TODO save to file
        print(options)
    except Exception as e:
        print(e)
