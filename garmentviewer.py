"""
    Loads maya interface for editing & testing template files
    Python 2.7 compatible
    * Maya 2018+
    * Qualoth
"""

# My modules
import mayaqltools as mymaya
reload(mymaya)

# -------------- Main -------------
if __name__ == "__main__":
    mymaya.qualothwrapper.load_plugin()
    try:
        mymaya.garmentUI.start_GUI()
    except Exception as e:
        print(e)
