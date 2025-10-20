import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

def get_connection_str():
    load_dotenv()

    required_vars = {
        'DB_USER': 'Database username',
        'DB_PASSWORD': 'Database password',
        'DB_HOST': 'Database host',
        'DB_PORT': 'Database port',
        'DB_NAME': 'Database name'
    }

    missing = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing.append(var)
    
    if missing:
        print('missing environment variables')
        for var in missing:
            print(var)

    connection_str = (
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )

    return connection_str

def create_db_engine(echo=False, pool_size=5, max_overflow=10):
    connection_str = get_connection_str()
    logger.info(f"Creating database engine: {os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}")

    engine = create_engine(
        connection_str,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=30,
        pool_recycle=3600,
        echo=echo
    )

    return engine

def test_connection():
    try:
        print('testing connection')
        engine = create_db_engine()

        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.scalar()

        engine.dispose()
        print("works")
        return True
    except Exception as e:
        print("doesn't work")
        return False
    
# dont wanna do this rn
# def get_db_info():
#     try:
#         engine = create_engine()

#     except Exception as e:
#         print(e)