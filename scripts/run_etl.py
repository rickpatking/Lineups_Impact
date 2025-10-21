import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
import logging

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

log_dir = project_root / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),              # Print to console
        logging.FileHandler(log_dir / 'etl_pipeline.log')  # Save to file
    ]
)

logger = logging.getLogger(__name__)

load_dotenv()

from src.etl.pipeline import process_season, process_single_game
from src.utils.db_connection import create_db_engine

def parse_args():
    parser = argparse.ArgumentParser(description='Run NBA Lineup Analysis ETL Pipeline')
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--game-id', type=str, help='Process single game (e.g., 0022300001)')
    group.add_argument('--season', type=str, help='Process full season (e.g., 2024-25)')

    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_args()

    logger.info("NBA LINEUP ANALYSIS ETL PIPELINE")
    try:
        if args.game_id:
            logger.info(f"Mode: Single Game ({args.game_id})")
            engine = create_db_engine()
            try:
                success = process_single_game(args.game_id, engine)
                if success:
                    print("Pipeline Successfully loaded game")
                    return 0
                else:
                    print("Pipeline Failed to load game")
                    return 1
            finally:
                logger.debug("Disposing database engine...")
                engine.dispose()
                # make sure to close the engine after use
        elif args.season:
            logger.info(f"Mode: Full Season ({args.season})")
            engine = create_db_engine()
            try: 
                success = process_season(args.season, engine)
                if success:
                    print("Pipeline Successfully loaded season")
                    return 0
                else:
                    print("Pipeline Failed to load season")
                    return 1
            finally:
                logger.debug("Disposing database engine...")
                engine.dispose()
    except KeyboardInterrupt:
        logger.warning("Pipeline interrupted by user (Ctrl+C)")
        return 130
    except Exception as e:
        logger.error(f"Error {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())