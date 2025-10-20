import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

DATA_DIR = PROJECT_ROOT / 'data'
RAW_DATA_DIR = DATA_DIR / 'raw'
PROCESSED_DATA_DIR = DATA_DIR / 'processed'
VALIDATION_DATA_DIR = DATA_DIR / 'validation'

SQL_DIR = PROJECT_ROOT / 'sql'
SCHEMA_DIR = SQL_DIR / 'schema'
QUERIES_DIR = SQL_DIR / 'queries'

LOGS_DIR = PROJECT_ROOT / 'logs'

for dir in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, LOGS_DIR]:
    dir.mkdir(parents=True, exist_ok=True)

DB_POOL_SIZE = 5
DB_MAX_OVERFLOW = 10
DB_POOL_TIMEOUT = 30
DB_POOL_RECYCLE = 3600
DB_BATCH_SIZE = 1000