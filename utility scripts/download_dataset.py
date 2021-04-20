from pathlib import Path
import wandb
import customconfig

system_props = customconfig.Properties('./system.json')

api = wandb.Api({'project': 'Garments-Reconstruction'})
artifact = api.artifact(name='jacket:latest')
filepath = artifact.download(Path(system_props['datasets_path']) / 'data_1250_jacket_210414-15-48-45')
