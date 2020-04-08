"""
    Qualoth scripts are written in MEL. 
    This module makes a python interface to them
    Note that's Python 2.7-friendly
"""

from maya import mel
from maya import cmds

# Note: the name is Maya-vesion dependent
# TODO auto detect maya version
plugin_name = 'qualoth_2020_x64'


def load_plugin():
    """
        Forces loading Qualoth plugin into Maya. Note that you need a license to use it!
        Inquire here: http://www.fxgear.net/vfxpricing
    """
    cmds.loadPlugin(plugin_name)


# -------- Wrappers -----------
# Make sure that Qualoth plugin is loaded before running any wrappers!

def qlCreateCollider(cloth, body):
    """
        Marks body as a collider object for cloth --
        eshures that cloth won't penetrate body when simulated
    """
    cmds.select([cloth, body])
    # Operates on selection
    mel.eval('qlCreateCollider()')
