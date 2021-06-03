# Running dataset generation

Before running generation, make sure that you are familiar with [setup](./Setting_up_generator.md) and tested your setup with [GarmentViever GUI](./Setting_up_generator.md#Preview-your-setup-in-GarmentViewer-GUI).

The process consists of three steps that need to be run sequentially:

* Sampling sewing pattern designs from template 
* Draping each over the base body (physics simulation)
* (if needed) perform 3D scan imitation on each of the meshes

More on each step below.

## Components of the generation system
> Run _help_(module) for even more detailed descriptions of corresponding python modules

### Dataset generator
In `datasetgenerator.py` module

2D pattern dataset generation from given templates. Allows to configure the generation by supplying Properties object.
Example usage of the generator is given in 
``` if __name__ == "__main__": ```
section of the file.

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
* The process does NOT override the initial meshes, but rather created new .obj files for corrupted versions.

## Optional (but helpful) utilities 
Found in [`utility scripts/`](../utility%20scripts/)
* [`gather_renders.py`](../utility%20scripts/gather_renders.py) is a small skript to copy all the simulation renders of each datapoint to one location for convenience of data review.
* [`all_data_has_all_files.py`](../utility%20scripts/all_data_has_all_files.py) tests if all datapoints in all datasets of your dataset folder are present and correctly structured (recommended to use after downloading the data or merging the datasets).
* [`maya_segmentaion_viz.py`](../utility%20scripts/maya_segmentaion_viz.py) a script to be executed within Maya environment to visualize segmentation of a mesh from a particular datapoint.
* [`merge_datasets.py`](../utility%20scripts/merge_datasets.py) merges two dataset folders that were produced from the same template into one data folder with single `dataset_properties.json` file. It's helpful to keep the data organized by garment type.
* [`crashes_to_unprocessed.py`](../utility%20scripts/crashes_to_unprocessed.py) small utility for cases when the simulation process of dataset produced a lot of crashed examples and those need to be re-simulating without revising the correct ones.


