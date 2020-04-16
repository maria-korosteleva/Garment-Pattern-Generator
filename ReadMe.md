# Generating synthetic dataset of 2D patterns

## Licensing 
This is work-in-progress, and licensing terms are not finalized. If you want to use this code, please, contact the authors. 

## Requirements
* Python >= 3.6. Might work with earler versions, but wasn't tested on those
* Maya 2018+ with Arnold and Qualoth
* for libraries, refer to import sections that are grouped at the beginning of each .py file. All libs can be simply installed with pip.

## Filesystem paths settings
Create system.json file in the root of this directory with your machine's file paths including
* path to pattern templated folder ('templates_path') 
* path for creating logs & putting new datasets to ('output')
Use system.template.json as a template. 

## Components of the generation system
Note: Run _help_(module) for detailed descriptions of python modules

### Pattern templates:
.json files containg parametrized patterns. 
* Examples are given in ./Patterns. 
* template_spec_with_comments.json contains a detailed description of the format

### 2D pattern instances  
In pattern package
Contain several wrappers of 2D pattern custom format
* Basic wrapper for loading & saving
* Visualozation wrapper for rendering a pattern to svg
* Randomization wrapper for deriving a sample from parametrized template

### Dataset generator
In datasetgenerator.py module

2D pattern dataset generation from given templates. Allows to configure the generation by supplying Properties object.
Example usage is given in 
``` if __name__ == "__main__": ```
section of the file

### Simulation
in datasim.py & simulation module

* Simulates each pattern in the dataset over a given human body object
* Uses Qualoth for Maya cloth simulation





