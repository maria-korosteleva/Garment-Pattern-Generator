from pathlib import Path
import customconfig
import wandb

system_props = customconfig.Properties('./system.json')

wandb.init(project='Garments-Reconstruction', job_type='dataset')

dataset = 'data_1000_pants_straight_sides_210105-10-49-02'
artifact = wandb.Artifact('dataset_1000_pants_straight_sides_210105-10-49-02', type='dataset')
# Add a file to the artifact's contents
datapath = Path(system_props['datasets_path']) / dataset
artifact.add_dir(str(datapath))
# Save the artifact version to W&B and mark it as the output of this run
wandb.run.log_artifact(artifact)



