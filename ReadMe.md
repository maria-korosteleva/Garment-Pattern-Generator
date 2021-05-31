<!--
*** With tips from https://github.com/othneildrew/Best-README-Template
-->


<!-- Header with Navigation -->
<br />
<p align="center">
  <h1 align="center">Generating Datasets of 3D Garments with Sewing Patterns</h1>

  <p align="center">
    Official implementation of <a href="">Generating Datasets of 3D Garments with Sewing Patterns</a>
    <br />
    <br />
    <!-- <a href="">Project Page</a>
    . -->
    <a href="">Dataset</a>
    ·
    <a href="#requirements">Requirements</a>
    ·
    <a href="#docs">How to use</a>
    ·
    <a href="#how-to-cite">How to cite</a>
    ·
    <a href="#contributions">Contributions</a>
    ·
    <a href="#contact">Contact us</a>
  </p>
</p>

> Add figure here

## Requirements

* Autodesk Maya 2018/2020 with Arnold
    * Qualoth version for Maya 2022 is not available at the moment of the main development
    > ☝ Arnold requires license to render simulated data without watermarks.
* [Qualoth 2020](https://www.qualoth.com/) cloth simulator.

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

## Docs

> To Add: on system.json file!

* [Sewing pattern template specification](docs/template_spec_with_comments.json) - spec example with comments to all the elements.
* [Configuring dataset generation](docs/Setting_up_generator.md) - from sewing pattern template to physics simulation components
* [Running data generation](docs/Running_generation.md) - getting all the steps right.


## How to cite

If you are using this system for your research, please, cite our paper

> Bibtex


## Contributions

>📋 To add: Pick a licence and describe how to contribute to your code repository. 

### ToDo
* Clarify documentation
* Reformat template spec description for easy reading
* Adding support for other curve types
* Body Pose variations
* Body Shape variations
* Fabric properties sampling
* Swithcing to Open Source cloth simulator

## Contact

For bug reports, feature suggestion, and code-related questions, please [open an issue](https://github.com/github_username/repo_name/issues). 

For other inquires, contact the authors: 

> To add

## Acknowledgements

* [Best-README-Template](https://github.com/othneildrew/Best-README-Template) for great ReadMe tips!
> To add