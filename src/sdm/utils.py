import pandas as pd
from ..config import config


def get_species_name(species_id: str):
    df = pd.read_csv(config["BIRD_LIST"])
    return df[df['SABAP2_number'] == int(species_id)]['SA_name'].values[0]