from pathlib import Path
import wandb
import customconfig

system_props = customconfig.Properties('./system.json')

api = wandb.Api({'project': 'Garments-Reconstruction'})
artifact = api.artifact(name='dataset_1000_pants_straight_sides_210105-10-49-02:latest')
filepath = artifact.download(Path(system_props['datasets_path']) / 'data_uni_1000_pants_straight_sides_210105-10-49-02')
