# Dataset setup components

## Pattern template
`./Patterns` contains exmaples of parametrized pattern templates that can be sampled to form a dataset of sewing patterns. 
* Each template is a .json file that sedcribes the structure of the base pattern and the way it could be changes (parametrization)
* `./Patterns/template_spec_with_comments.json` contains a detailed description of the format used to describe pattern pemplates

## Body (3D model to drape garments on)
`./Bodies` contain example `.obj` files with 3D models used to drape a garment on
* One dataset uses only one base model (at this stage of development)
* In general, our system allows to use any kind of  3D model for sewing patterns to be draped over
    * However, our example patterns are designed to be draped on the average female body we borrow from [SMPL statistical body model|https://smpl.is.tue.mpg.de/] in T-pose: `f_smpl_template.obj` 

## Rendering setup (optional)
`./Scenes` contain example scenes that can be used to create good-looking renders of the draping result of each datapoint. Usage of scenes is options, and a default simple setup will be created if no scene file is provided for data simulation pipeline.

A scene is a Maya file that contains the following elements:
* Light sources
* Cameras (any number) 
    * At render time, images from all the available cameras in the scene will be created
* Stage geometry -- could be as complicated as needed
* Configured materials for stage, body, and garment

*NOTE:* When developing a new rendering setup, follow the scaling, groupings, and naming conventions from the example scenes.

*NOTE:* As other dataset components, scenes can be tested with GUI `garmentviewer.py` in Maya.

## Dataset Simulation pipeline config file
`./Sim_props` contains configuration files that describe dataset simulation process setup.

On the high level, every config contains the following
* Name of the base 3D model (body) file to use for draping
* Render setup with the name of the scene file to use (if any) and a desired resulution of output images
* Material properties of garment fabric & body to be used for physics simulation
* Geometry resolution multiplier (the larger -- the higher the final res of a garment 3D model)
* Different thresholds to control the sensitivity of simulation quality checks
    * Simulation quality checks are designed to filter out garments with failed simulations to avoid biasing the training a dataset will be used for
    * Examples of bad simulation results: skirt sliding down to the legs; heavy self-intersections, etc.

## Scan imitation configuration

> to Add