import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.db_connection import create_db_engine
from src.etl.pipeline import process_season
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/etl_pipeline.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

print("="*70)
print("RELOADING ALL DATA WITH FIXED LINEUP TRACKER")
print("="*70)

engine = create_db_engine()

print("\nThe lineup_stints table has been cleared.")
print("play_by_play, games, players, and teams data is still intact.")
print("\nStarting to reload lineup stints for all games...")
print("This will take a while due to NBA API rate limiting.\n")

try:
    # Process the 2024-25 season
    # The pipeline will skip already-loaded games (based on play_by_play table)
    # but will regenerate lineup_stints for all games
    process_season('2024-25', engine, batch_size=10)

    print("\n" + "="*70)
    print("DATA RELOAD COMPLETE!")
    print("="*70)

except Exception as e:
    logger.error(f"Error during data reload: {e}", exc_info=True)
    print(f"\n[ERROR] Data reload failed: {e}")
    print("Check logs/etl_pipeline.log for details")

finally:
    engine.dispose()
