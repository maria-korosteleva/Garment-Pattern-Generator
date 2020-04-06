import maya.cmds

# My module
# Needs to be avalible through PATH env. variable (or maybe in Maya workspace)
import pattern
from pathlib import Path


class MayaPattern(pattern.BasicPattern):
    """
    Extention of the Basic pattern wrapper that supports 
        * import panel to Maya scene TODO
        * cleaning imported stuff TODO
        * Basic operations on panels in Maya TODO
    """
    def __init__(self, pattern_file):
        super().__init__(pattern_file)
    
    def load(self):
        print("All panels loaded to Maya")


if __name__ == "__main__":
    pattern = MayaPattern(
        Path("C:/Users/LENOVO/Desktop/Garment-Pattern-Estimation/data_generation/Patterns/skirt_per_panel.json")
    )
    pattern.load()
