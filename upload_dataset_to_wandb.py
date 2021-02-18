from pathlib import Path
import customconfig
import wandb

system_props = customconfig.Properties('./system.json')

wandb.init(project='Garments-Reconstruction', job_type='dataset')

dataset = 'data_uni_1000_tee_200527-14-50-42_regen_200612-16-56-43'
artifact = wandb.Artifact('dataset_1000_tee_200527-14-50-42_regen_200612-16-56-43', type='dataset')
# Add a file to the artifact's contents
datapath = Path(system_props['datasets_path']) / dataset
artifact.add_dir(str(datapath))
# Save the artifact version to W&B and mark it as the output of this run
wandb.run.log_artifact(artifact)



