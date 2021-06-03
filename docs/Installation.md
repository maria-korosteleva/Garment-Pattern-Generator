# Installation Instructions

## Dependencies

* Autodesk Maya 2018/2020 with Arnold
    * Qualoth version for Maya 2022 is not available at the moment of the main development

    >☝ Arnold requires license to render simulated data without watermarks.
* [Qualoth 2020](https://www.qualoth.com/) cloth simulator 

### Maya Python API Environment
* Numpy (for Python 2.7)
    * The process for installation is desribed in guides like [this one](https://forums.autodesk.com/t5/maya-programming/guide-how-to-install-numpy-scipy-in-maya-windows-64-bit/td-p/5796722)

### Generic Python Environment
* Python 3.6+
* numpy
* scipy
* [svglib](https://pypi.org/project/svglib/)
* [svgwrite](https://pypi.org/project/svgwrite/)
* psutil
* wmi
    * [Troubleshooting 'DLL load failed while importing win32api'](https://stackoverflow.com/questions/58612306/how-to-fix-importerror-dll-load-failed-while-importing-win32api) error on Win

## Setting up 
### Environmental variables

* Add `./packages` to `PYTHONPATH` on your system for correct importing of our custom modules.
### Local paths setup

Create system.json file in the root of this directory with your machine's file paths using `system.template.json` as a template. 
`system.json` should include the following: 
* Path for creating logs at (including generated data from dataset generation routined & NN predictions) (`'output'`)
* Path to the folder with (generated) garment datasets (`'datasets_path'`)

* Data generation & Simulation resources  (default to subdirectories of `./data_generation`)
    * path to pattern templates folder (`'templates_path'`) 
    * path to folder containing body files (`'bodies_path'`)
    * path to folder containing rendering setup (scenes) (`'scenes_path'`)
    * path to folder with simulation\rendering configurations (`'sim_configs_path'`)