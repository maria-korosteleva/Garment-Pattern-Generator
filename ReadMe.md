# Generating synthetic dataset of 2D patterns

## Licensing 
This is work-in-progress, and licensing terms are not finalized. If you want to use this code, please, contact the authors. 

## Requirements
* Python >= 3.6. Might work with earler versions, but wasn't tested on those
* for libraries, refer to import sections that are grouped at the beginning of each .py file. All libs can be simply installed with pip.

## Components of the generation system
### Dataset generator

In DatasetGenerator.py module

2D pattern dataset generation from given templates. Allows to configure the generation by supplying DatasetProperties object.
Example usage is given in 
``` if __name__ == "__main__": ```
section of the file

### 2D pattern instance  
In pattern.py module.

Describes a sample of parametrized 2D pattern space defined by a pattern template. Can be used to derive a sample and convert it to representations needed by other parts of the system.

### Pattern templates:
.json files containg parametrized patterns. Examples are given in ./Patterns. 

_Detailed specification of the format will be provided later_



