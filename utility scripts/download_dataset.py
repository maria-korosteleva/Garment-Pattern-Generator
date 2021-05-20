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
    'jacket_hood:latest': 'data_1000_jacket_hood_210430-15-12-19',
    # 'jacket_hood:v4': 'merged_jacket_hood_1700_210425-21-23-19',
    'tee_sleeveless:latest': 'data_650_tee_sleeveless_210429-10-55-00',  # v2 I already have!
    'jacket:latest': 'data_650_jacket_210504-11-07-51',
    # 'jacket:v2': 'merged_jacket_1550_210420-16-54-04',
    'wb_dress_sleeveless:latest': 'data_1050_wb_dress_sleeveless_210420-13-00-16',
    'skirt_2_panels:latest': 'data_500_skirt_2_panels_210503-13-37-39',
    'wb_pants_straight:latest': 'data_350_wb_pants_straight_210506-18-50-3',
    # 'skirt_8_panels:v1': 'merged_skirt_8_panels_950_210412-16-11-33',
    'skirt_8_panels:latest': 'data_50_skirt_8_panels_210511-12-56-59'
}

api = wandb.Api({'project': 'Garments-Reconstruction'})
for key in to_download:
    artifact = api.artifact(name=key)
    filepath = artifact.download(Path(system_props['datasets_path']) / to_download[key])
    # filepath = artifact.download(Path(system_props['output']) / to_download[key])
