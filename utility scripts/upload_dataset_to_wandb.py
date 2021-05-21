from pathlib import Path
import customconfig
import wandb

system_props = customconfig.Properties('./system.json')

to_upload = {
    'merged_wb_pants_straight_1500_210521-16-30-57': 'wb_pants_straight',
    'merged_skirt_2_panels_1200_210521-16-46-27': 'skirt_2_panels',
    'merged_jacket_2200_210521-16-55-26': 'jacket',
    'merged_tee_sleeveless_1800_210521-17-10-22': 'tee_sleeveless',
    'merged_wb_dress_sleeveless_2600_210521-17-26-08': 'wb_dress_sleeveless',
    'merged_jacket_hood_2700_210521-17-47-44': 'jacket_hood'
}

for dataset, art_name in to_upload.items():
    wandb.init(project='Garments-Reconstruction', job_type='dataset')

    artifact = wandb.Artifact(art_name, type='dataset', description=dataset)
    # Add a file to the artifact's contents
    datapath = Path(system_props['datasets_path']) / dataset
    artifact.add_dir(str(datapath))
    # Save the artifact version to W&B and mark it as the output of this run
    wandb.run.log_artifact(artifact)

    wandb.finish()  # sync all data before moving to next dataset



