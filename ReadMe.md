# Generating synthetic dataset of 2D patterns

Create dataset of garments with 3D draped geometry and corresponding 2D patterns. 

## Extra Requirements
* Maya 2018+ with Arnold and Qualoth
    * NOTE Arnold requires license to render simulated data without watermarks using datasim.py\datasim_runner.sh. 
    * A single-user Arnold license requires re-activation (logging-in) each time PC is rebooted
* for libraries, refer to import sections that are grouped at the beginning of each .py file. All libs can be simply installed with pip.

## Dataset setup components
### Pattern template
`./Patterns` contains exmaples of parametrized pattern templates that can be sampled to form a dataset of sewing patterns. 
* Each template is a .json file that sedcribes the structure of the base pattern and the way it could be changes (parametrization)
* `./Patterns/template_spec_with_comments.json` contains a detailed description of the format used to describe pattern pemplates

### Body (3D model to drape garments on)
`./Bodies` contain example `.obj` files with 3D models used to drape a garment on
* One dataset uses only one base model (at this stage of development)
* In general, our system allows to use any kind of  3D model for sewing patterns to be draped over
    * However, our example patterns are designed to be draped on the average female body we borrow from [SMPL statistical body model|https://smpl.is.tue.mpg.de/] in T-pose: `f_smpl_template.obj` 

### Rendering setup (optional)
`./Scenes` contain example scenes that can be used to create good-looking renders of the draping result of each datapoint. Usage of scenes is options, and a default simple setup will be created if no scene file is provided for data simulation pipeline.

A scene is a Maya file that contains the following elements:
* Light sources
* Cameras (any number) 
    * At render time, images from all the available cameras in the scene will be created
* Stage geometry -- could be as complicated as needed
* Configured materials for stage, body, and garment

*NOTE:* When developing a new rendering setup, follow the scaling, groupings, and naming conventions from the example scenes.

*NOTE:* As other dataset components, scenes can be tested with GUI `garmentviewer.py` in Maya.

### Dataset Simulation pipeline config file
`./Sim_props` contains configuration files that describe dataset simulation process setup.

On the high level, every config contains the following
* Name of the base 3D model (body) file to use for draping
* Render setup with the name of the scene file to use (if any) and a desired resulution of output images
* Material properties of garment fabric & body to be used for physics simulation
* Geometry resolution multiplier (the larger -- the higher the final res of a garment 3D model)
* Different thresholds to control the sensitivity of simulation quality checks
    * Simulation quality checks are designed to filter out garments with failed simulations to avoid biasing the training a dataset will be used for
    * Examples of bad simulation results: skirt sliding down to the legs; heavy self-intersections, etc.

## Generation steps
* Creating \ choosing the parametrized template
    * `garmentviewer.py` is for fast visualization of templates to help with the process
* Generating dataset of randomized garment patterns (with `datagenerator.py`)
* Simulating each pattern in the dataset with `datasim.py` or `datasim_runner.sh` 
    * `datasim_runner.sh` is a wrapper that is able to auto-restart data processing in case of Maya crashes \ hangs 
* Removing barely visible faces of resulting meshed to imitate 3D scanning artifacts with `datascan.py`


## Components of the generation system
Note: Run _help_(module) for detailed descriptions of python modules

### Garment Viewer
`garmentviewer.py` is to be run withing Maya (Python scripting). 

It provides simple UI for viewing a parametrized garment template, test parameter values, simulation process & rendering setup.

*NOTE:* make sure to add `Garment Pattern Estimation/packages/` directory to `PYTHONPATH` evironment variable to make the custom modules available in Maya

### Dataset generator
In `datasetgenerator.py` module

2D pattern dataset generation from given templates. Allows to configure the generation by supplying Properties object.
Example usage is given in 
``` if __name__ == "__main__": ```
section of the file

### Simulation
`datasim.py` & `mayaqltools` package

* Simulates each pattern in the dataset over a given human body object
* Uses Qualoth for Maya cloth simulation
* It is designed to run with Mayapy as standalone interpreter 
* Command line arguments are the dirs\files basenames given that system.json is properly created.

Example usage from command line:
```
<Maya Installation path>/bin/mayapy.exe "./datasim.py" --data <dataset_name> --minibatch <size>  --config <simulation_props.json>
```

#### **Running simulation of large-scale datasets over Maya\Qualoth crashes**

`dataset_runner.sh` script is given for convence of processing large amounts of garment patters over long period of time. The main feature is detection of dataset sim processing hangs \ crashes and automatic resume of dataset processing in case of such events. 

### Imitating 3D scanning artifacts

`datascan.py` 
* is designed to work on datasets that passed the simulation steps. 
* It modifies every 3D garment mesh to imitate missing geometry due to 3D scanning, and saves it as a separate file in the datapoint folder

### Additional processing
* `gather_renders.py` is a small skript to copy all the simulation renders in the dataset to one location for convenience of data review.


