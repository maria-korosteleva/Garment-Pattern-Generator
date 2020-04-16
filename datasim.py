"""
    Run the simulation af a dataset
    Note that it's Python 2.7 friendly
"""

import simulation as mysim
reload(mysim)


if __name__ == "__main__":
    path = 'C:/Users/LENOVO/Desktop/Garment-Pattern-Estimation/data_generation/Patterns/'
    sub = 'basic skirt/'
    
    mysim.single_file_sim(
        path + sub + 'skirt_maya_coords.json', 
        path + 'f_smpl_templatex300.obj', 
        path + sub)

    # mysim.single_file_sim(path + 'skirt_maya_penetrate.json', 'F:/f_smpl_templatex300.obj', 'F:/GK-Pattern-Data-Gen/Sims')
