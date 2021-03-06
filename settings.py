from dotenv import load_dotenv
import os
load_dotenv()

DV_BASE_URL = os.getenv('DV_BASE_URL') or 'https://api.dataviper.io'
API_TOKEN = os.getenv('API_TOKEN')
OUTPUT_DIR = os.getenv('OUTPUT_DIR') or 'output'
MASTER_LIST_DIR = os.getenv('MASTER_LIST_DIR') or 'master-list'
PARSE_DIR = os.getenv('PARSE_DIR') or 'parse'
COMBO_DIR = os.getenv('COMBO_DIR') or 'combo'
AVATAR_DIR = os.getenv('AVATAR_DIR') or 'avartar'
ARCHIVE_DIR = os.getenv('ARCHIVE_DIR') or 'archive'
IMPORT_DIR = os.getenv('IMPORT_DIR') or 'import'
OFFSITE_DEST = os.getenv('OFFSITE_DEST') or 'b2:/ViperStorage/forums/2020/file'
LOG_DIR = os.getenv('LOG_DIR') or 'log'
PYTHON_BIN = os.getenv('PYTHON_BIN') or 'python'
