## Components of the generation system
Note: Run _help_(module) for detailed descriptions of python modules

### Garment Viewer
> Move to Setting up?

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

### Helpful itilities processing 
* `gather_renders.py` is a small skript to copy all the simulation renders in the dataset to one location for convenience of data review.
