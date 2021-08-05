"""
    Loads maya interface for editing & testing template files
    Python 2.7 compatible
    * Maya 2018+
    * Qualoth
"""

from maya import cmds

# My modules
import mayaqltools as mymaya
reload(mymaya)

# -------------- Main -------------
if __name__ == "__main__":
    print('Load plugins')
    mymaya.qualothwrapper.load_plugin()
    cmds.loadPlugin('mtoa.mll')  # https://stackoverflow.com/questions/50422566/how-to-register-arnold-render
    cmds.loadPlugin('objExport.mll')  # same as in https://forums.autodesk.com/t5/maya-programming/invalid-file-type-specified-atomimport/td-p/9121166

    try:
        mymaya.garmentUI.start_GUI()
    except Exception as e:
        print(e)
