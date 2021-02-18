from pathlib import Path
import wandb
import customconfig

system_props = customconfig.Properties('./system.json')

api = wandb.Api({'project': 'Garments-Reconstruction'})
artifact = api.artifact(name='dataset_1000_tee_200527-14-50-42_regen_200612-16-56-43:latest')
filepath = artifact.download(Path(system_props['datasets_path']) / 'data_uni_1000_tee_200527-14-50-42_regen_200612-16-56-43')
