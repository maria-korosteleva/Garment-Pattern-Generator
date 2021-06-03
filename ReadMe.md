
# Generating Datasets of 3D Garments with Sewing Patterns

Official implementation of [Generating Datasets of 3D Garments with Sewing Patterns]() [Link to be added upon sharing on arxive \ publication].

## Dataset
> Reference to our public dataset of Garment 3D models with Sewing patterns (will be added upon availiblity)

## Docs
Provided in `./docs` folder

* [Dependencies and Installation instructions](docs/Installation.md)
* [Configuring dataset generation](docs/Setting_up_generator.md) - from sewing pattern template to physics simulation components.
* [Running data generation](docs/Running_generation.md) - getting all the steps right & additional helpful operations.
* [Sewing pattern template specification](docs/template_spec_with_comments.json) - spec example with comments to all the elements.

## How to cite

If you are using this system for your research, please, cite our paper

> Bibtex will be added here

## Contact

For bug reports, feature suggestion, and code-related questions, please [open an issue](https://github.com/github_username/repo_name/issues). 

For other inquires, contact the authors: 

* Maria Korosteleva ([mariako@kaist.ac.kr](mailto:mariako@kaist.ac.kr)) (Main point of contact). 

* Sung-Hee Lee ([sunghee.lee@kaist.ac.kr](mailto:sunghee.lee@kaist.ac.kr)).

## Contributions

We welcome contributions of bug fixes, features, and new assets (templates, scenes, body models, simulation properties). Please, create a [Pool Request]() if you wish to contribute.

>☝ All the new code and assets will be shared here under the [MIT license](LICENSE). Please, ensure that you hold the rights to distribute your artifacts like that. The authors do not take the responsibility of licensing violations for artifacts contributed by users. Thank you for your understanding 😊

## ToDo (future work)
* Reformat template spec description for easy reading
* Allow to turn off or chose simpler renderer for getting the datasets faster
* Adding support for other curve types
* Body Pose variations
* Body Shape variations
* Fabric properties sampling
* Swithcing to Open Source cloth simulator

## Acknowledgements
* Big thanks to the developers of [SMPL](https://smpl.is.tue.mpg.de/) for generously sharing their Body Model with the community (licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)). We are using their average female model as a human body example.