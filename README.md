# SDM for Southern African birds in Africa

A pipeline for generating species distribution estimations from a variety of data sources. This was developed in collaboration with the [Science and Innovationd department at BirdLife South Africa](https://www.birdlife.org.za/what-we-do/science-and-innovation/).

Observation data was obtained from [SABAP2](https://sabap2.birdmap.africa/), [iNaturalist](https://inaturalist.org/) and [eBirds](https://ebird.org/home) for the African continent and covariate data was obtained from [WorldClim](https://www.worldclim.org/data/bioclim.html) and several [Google Earth Engine](https://developers.google.com/earth-engine/datasets/) datasets.

The geographic sampling unit employed in this research is the 'pentad,' corresponding to a grid cell measuring 5 minutes in both latitude and longitude. Each pentad covers an area of approximately 80 square kilometers, depending on latitude and longitude. We use this as this is the geographic sampling scale of the SABAP2 project.

## Data
The datasets have all been added to Kaggle, at different stages of aggregation, to make it easy for anyone to download them and run this pipeline. There are commands that can be run in this pipeline that will download all of the datasets.

### SABAP2
SABAP2 has a rigorous sampling and vetting protocol, but the scale is course and coverage across the continent is uneven.

### iNaturalist
Only research grade observations were selected from iNaturalist. This was downloaded via [GBIF](https://www.gbif.org/occurrence/download/0034165-230810091245214). A total of 534,377 occurrences. This data is hosted on Kaggle over [here](https://www.kaggle.com/datasets/manatok/bird-observations).

### eBirds
The eBirds dataset contains records with the highest risk of missclassification. This data is only used to improve the confidence of the pseudo-absence records. This was downloaded via [GBIF](https://www.gbif.org/occurrence/download/0034248-230810091245214). A total of 15,528,826 occurrences. This data is hosted on Kaggle over [here](https://www.kaggle.com/datasets/manatok/bird-observations-ebird).

### WorldClim
WorldClim is a database of high spatial resolution global weather and climate data. This dataset has been pre aggregated at the pentad level and is hosted on Kaggle over [here](https://www.kaggle.com/datasets/manatok/worldclim).

### Google Earth Engine Datasets
A number of bioclimatic datasets were downloaded via Google Earth Engine scripts and aggreated at the pentad layer. This data is hosted on Kaggle over [here](https://www.kaggle.com/datasets/manatok/africa-bioclim-google-ee). The script which defines all of the images and layers can be found over [here](https://github.com/manatok/sdm/blob/main/src/google_ee/mean_by_pentad.js).

### Combined Datasets
All of the above datasets are combined, such that the final files used by the model are:
1. verified_observations.feather - This is a pentad x sabap_species_id matrix contains the sum of the SABAP2 and iNat datasets.
2. unverified_observations.feather - At this stage, this only contains the eBird dataset. This this also has the shape: pentad x sabap_species_id.
3. combined_covariates.feather - This is a combination of the WorldClim and Google Earth Engine data and is in the shape pentad x covariates.

This data is hosted on Kaggle over [here](https://www.kaggle.com/datasets/manatok/african-bird-observations-and-covariates-by-pentad).



## Setting Up the Virtual Environment

1. **Ensure Python is Installed**:
   Before you start, make sure you have Python 3 installed on your system.

2. **Navigate to the Project Directory**:
   Open your terminal or command prompt and navigate to the project directory:
   ```
   cd sdm/
   ```

3. **Create a Virtual Environment**:
   To create a virtual environment, run:
   ```
   python -m venv venv
   ```

4. **Activate the Virtual Environment**:
   Depending on your operating system, use one of the following commands:

   **Linux/Mac**:
     ```
     source venv/bin/activate
     ```
     **Windows**:
     ```
     .\venv\Scripts\activate
     ```

5. **Install the Dependencies**:
   With the virtual environment activated, install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
6. **Download Kaggle API key**:
   In order to use the scripts to download the datasets you will need to register on Kaggle and download the API key. Follow the instructions found over [here](https://github.com/Kaggle/kaggle-api) and ensure that the `KAGGLE_CONFIG_DIR` environment variable is set.

## Usage

After setting up the environment, you can execute the pipeline using the CLI.

1. **Download the data**:
   The fastest way to get up and running is to download the pre aggregated and combined datasets.
   ```
   python -m src.run download-all-data
   ```

2. **Run the pipeline for a species**:
   Generate the species distribution map and occurance probabilities per pentad.
   ```
   python -m src.run generate-distribution --species_id=<species_id>
   ```

   This will generate:
   1. Distribution maps in `output/maps/species_id_...`
   2. Pentad probabilities in `output/pentad_probabilities/species_id_...`
   3. Model scores in `output/training_results.csv`

3. **Run the pipeline for ALL species**:
   This makes use of the file located in `data/lists/BirdList.csv`.
   ```
   python -m src.run generate-all-distributions
   ```

   This will generate results for all species in the list that:
   1. Have the `inat_name` column populated.
   2. Have at least 30 pentads of observations.

## Implementation details
