from pathlib import Path
import customconfig
import wandb

system_props = customconfig.Properties('./system.json')

wandb.init(project='Garments-Reconstruction', job_type='dataset')

dataset = 'data_1050_jacket_hood_210415-17-01-48'
artifact = wandb.Artifact('jacket_hood', type='dataset')
# Add a file to the artifact's contents
datapath = Path(system_props['datasets_path']) / dataset
artifact.add_dir(str(datapath))
# Save the artifact version to W&B and mark it as the output of this run
wandb.run.log_artifact(artifact)



