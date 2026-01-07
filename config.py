# config.py
import os

# Get the absolute path of the project root directory
project_root = os.path.dirname(os.path.abspath(__file__))

# Configuration settings
UPLOAD_FOLDER = os.path.join(project_root, 'uploads')
DOWNLOAD_FOLDER = os.path.join(project_root, 'downloads')
SUBSTANCE_DATA_PATH = os.path.join(project_root, 'data/SubstanceList.csv')
GLOVE_DATA_PATH = os.path.join(project_root, 'data/GloveData.csv')
SELECT_LIST_PATH = os.path.join(project_root, 'data/SelectList.csv')
TEMPLATE_CSV_PATH = os.path.join(project_root, 'data/template.csv')
