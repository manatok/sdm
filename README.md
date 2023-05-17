# Your Data Processing Pipeline

This repository contains a data processing pipeline that can be executed from the command line.

## Setting Up the Virtual Environment

1. **Ensure Python is Installed**:  
   Before you start, make sure you have Python 3 installed on your system.

2. **Navigate to the Project Directory**:  
   Open your terminal or command prompt and navigate to the project directory:
   ```
   cd BLSA_SDM
   ```

3. **Create a Virtual Environment**:  
   To create a virtual environment, run:
   ```
   python -m venv venv
   ```

4. **Activate the Virtual Environment**:  
   Depending on your operating system, use one of the following commands:
   - **Linux/Mac**:
     ```
     source venv/bin/activate
     ```
   - **Windows**:
     ```
     .\venv\Scripts\activate
     ```

5. **Install the Dependencies**:  
   With the virtual environment activated, install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

After setting up the environment, you can execute the pipeline using the CLI.

To process a species, use:
```
python src/sdm/entrypoint.py process_species --species_name "SPECIES_NAME"
```
Replace `SPECIES_NAME` with the name of the species you want to process.

## Adding dependencies
To install the dependency locally
   ```
   pip install dependency
   ```

To add the dependency to the requirements.txt:
   ```
   pip freeze > requirements.txt
   ```
# sdm
Bird Species Distribution Modelling
