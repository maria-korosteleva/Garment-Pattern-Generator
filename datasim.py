"""
    Run the simulation af a dataset
    Note that it's Python 2.7 friendly
"""

import simulation as mysim


if __name__ == "__main__":
    mysim.single_file_sim(
        'C:/Users/LENOVO/Desktop/Garment-Pattern-Estimation/data_generation/Patterns/skirt_maya_coords.json',
        'F:/f_smpl_templatex300.obj',
        'F:/GK-Pattern-Data-Gen/Sims'
    )
