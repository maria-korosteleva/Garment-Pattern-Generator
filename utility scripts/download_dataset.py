from pathlib import Path
import wandb
import customconfig

system_props = customconfig.Properties('./system.json')

# name:version in wandb : name to save to
to_download = {
    # 'jacket_hood_sleeveless-test:latest': 'test_150_jacket_hood_sleeveless_210331-11-16-33', 
    # 'skirt_waistband-test:latest': 'test_150_skirt_waistband_210331-16-05-37',
    # 'jacket_sleeveless-test:v0': 'test_150_jacket_sleeveless_210331-15-54-26',
    # 'dress-test:v0': 'test_150_dress_210401-17-57-12',
    # 'jumpsuit-test:v0': 'test_150_jumpsuit_210401-16-28-21',
    # 'wb_jumpsuit_sleeveless-test:v0': 'test_150_wb_jumpsuit_sleeveless_210404-11-27-30',
    # 'tee_hood-test:v0': 'test_150_tee_hood_210401-15-25-29'
    'multi-data:v66': 'Tee-JS-segment-shuffle-orderless-125',
    'multi-data:v67': 'Tee-JS-segment-shuffle-orderless-25',
}

api = wandb.Api({'project': 'Garments-Reconstruction'})
for key in to_download:
    artifact = api.artifact(name=key)
    # filepath = artifact.download(Path(system_props['datasets_path']) / to_download[key])
    filepath = artifact.download(Path(system_props['output']) / to_download[key])
