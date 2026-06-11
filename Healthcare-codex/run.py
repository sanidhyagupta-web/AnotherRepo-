"""
run.py — Starts all pipeline workers then seeds mock records and waits.

Usage:
  python run.py             # start workers + seed 20 records
  python run.py --seed 50   # seed 50 records
  python run.py --workers   # workers only, no seeding
"""
import argparse
import logging
import signal
import sys
import time

from db.database import init_db
from workers.parser_worker import ParserWorker
from workers.markdown_worker import MarkdownWorker
from workers.chunking_worker import ChunkingWorker
from workers.pii_worker import PiiWorker
from workers.embedding_worker import EmbeddingWorker
from workers.keyword_index_worker import KeywordIndexWorker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)-25s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/ingestion.log"),
    ],
)
logger = logging.getLogger("run")


def main():
    parser = argparse.ArgumentParser(description="Healthcare Semantic Search — Ingestion Pipeline")
    parser.add_argument("--seed", type=int, default=20, help="Number of mock records to seed (0 = skip)")
    parser.add_argument("--workers", action="store_true", help="Start workers only, skip seeding")
    args = parser.parse_args()

    logger.info("Initialising database...")
    init_db()

    workers = [
        ParserWorker(),
        MarkdownWorker(),
        ChunkingWorker(),
        PiiWorker(),
        EmbeddingWorker(),
        KeywordIndexWorker(),
    ]

    for w in workers:
        w.start()
    logger.info("All %d pipeline workers running", len(workers))

    if not args.workers and args.seed > 0:
        logger.info("Seeding %d mock records (workers will process them)...", args.seed)
        # Import here so workers are running before we enqueue
        from scripts.seed_mock_records import seed
        seed(args.seed)

    def _shutdown(sig, frame):
        logger.info("Received shutdown signal — stopping workers")
        for w in workers:
            w.stop()
        logger.info("All workers stopped. Goodbye.")
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    logger.info("Pipeline running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        _shutdown(None, None)


if __name__ == "__main__":
    main()
