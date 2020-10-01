# CUSL alerts migration
Clean-up allergies exports at Cliniques Universitaires Saint-Luc to import the content into the new EMR


How to run the program
======================

How to install the program
--------------------------

Install Python on your platform, then initiate the virtual environment using Poetry which will install all the required dependencies:

```
python -m pip install --user pipx
pipx install poetry
poetry install
```

Running the program
-------------------

The alert file must be deposited in the `Data` folder.
--> There must be only this file in the folder.
--> This file must be an Excel file (".xlsx").

Run the script:
```
cd Script
poetry run python Script_singleFile.py
```

The result of the script will be saved in the folder `Script\output\`.
--> If it doesn't exist, it will be created automatically.

Notice: the script may take several minutes to run.
