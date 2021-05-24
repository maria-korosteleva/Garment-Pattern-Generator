from pathlib import Path
import customconfig
import wandb

system_props = customconfig.Properties('./system.json')

to_upload = {
    # 'merged_dress_sleeveless_2550_210429-13-12-52': 'dress_sleeveless',
    # 'merged_jumpsuit_sleeveless_2000_210429-11-46-14': 'jumpsuit_sleeveless',
    # 'merged_skirt_8_panels_1000_210521-16-20-14': 'skirt_8_panels',
    # 'merged_wb_pants_straight_1500_210521-16-30-57': 'wb_pants_straight',
    # 'merged_skirt_2_panels_1200_210521-16-46-27': 'skirt_2_panels',
    # 'merged_jacket_2200_210521-16-55-26': 'jacket',
    # 'merged_tee_sleeveless_1800_210521-17-10-22': 'tee_sleeveless',
    # 'merged_wb_dress_sleeveless_2600_210521-17-26-08': 'wb_dress_sleeveless',
    'merged_jacket_hood_2700_210521-17-47-44': 'jacket_hood',
    # 'test_150_jacket_hood_sleeveless_210331-11-16-33': 'jacket_hood_sleeveless-test', 
    # 'test_150_skirt_waistband_210331-16-05-37': 'skirt_waistband-test',
    # 'test_150_jacket_sleeveless_210331-15-54-26': 'jacket_sleeveless-test',
    # 'test_150_dress_210401-17-57-12': 'dress-test',
    # 'test_150_jumpsuit_210401-16-28-21': 'jumpsuit-test',
    # 'test_150_wb_jumpsuit_sleeveless_210404-11-27-30': 'wb_jumpsuit_sleeveless-test',
    # 'test_150_tee_hood_210401-15-25-29': 'tee_hood-test' 
}

for dataset, art_name in to_upload.items():
    wandb.init(project='Garments-Reconstruction', job_type='dataset')

    artifact = wandb.Artifact(art_name, type='dataset', description='Mesh clean')
    # Add a file to the artifact's contents
    datapath = Path(system_props['datasets_path']) / dataset
    artifact.add_dir(str(datapath))
    # Save the artifact version to W&B and mark it as the output of this run
    wandb.run.log_artifact(artifact)

    wandb.finish()  # sync all data before moving to next dataset



